"""
Swin2SR Service - Super Resolution Service
Based on Swin Transformer V2 and Swin2SR
Supports cascade super-resolution for arbitrary scale factors
"""
import os
import io
import base64
import time
from typing import Dict, Optional, Tuple
from PIL import Image
import torch
import numpy as np


class Swin2SRService:
    """
    Swin2SR Service - Provides image super-resolution functionality
    
    Features:
    - Supports X2, X4, X8, X16 super-resolution
    - GPU acceleration (CUDA)
    - Cascade super-resolution for arbitrary scales
    - Lanczos fallback for small images
    """
    
    # Cascade configuration for different scale factors
    CASCADE_CONFIG = {
        2: [2],           # X2: Direct X2 model
        4: [4],           # X4: Direct X4 model
        8: [2, 4],        # X8: Cascade X2 then X4 (2×4=8)
        16: [4, 4],       # X16: Cascade X4 then X4 (4×4=16)
    }
    
    def __init__(self, sr_model_type: str = "auto", target_scale: int = 4):
        # Configuration from environment variables
        self.model_path = os.getenv("SWIN2SR_MODEL_PATH", "./weights/swin2sr")
        self.base_scale = int(os.getenv("SWIN2SR_SCALE", "4"))
        self.target_scale = target_scale  # Target scale factor
        self.use_gpu = os.getenv("SWIN2SR_USE_GPU", "true").lower() == "true"
        
        # T4 优化参数（参考 CSDN 教程）
        self.tile_size = 384  # T4 最优平衡点
        self.tile_overlap = 32  # 重叠区域，避免块边界伪影
        self.max_input_dim = 512  # 输入 > 512 就分块
        self.max_output_dim = 2000  # 输出 > 2000 就分块
        self.safe_size = 1024  # Safe processing size
        self.max_output_size = 4000  # Maximum output size
        
        # 调试：打印传入的 sr_model_type
        print(f"[Swin2SR.__init__] 传入的 sr_model_type: '{sr_model_type}' (type={type(sr_model_type).__name__})")
        print(f"[Swin2SR.__init__] sr_model_type is None: {sr_model_type is None}")
        print(f"[Swin2SR.__init__] sr_model_type is empty: {sr_model_type == '' if isinstance(sr_model_type, str) else 'N/A'}")
        
        # 移除 Auto Mode - 强制要求传入有效的 model_type
        valid_model_types = ["compressed", "classical", "realworld"]
        if sr_model_type is None or sr_model_type == "" or sr_model_type == "auto":
            raise ValueError(
                f"Invalid model_type: '{sr_model_type}'. "
                f"Must be one of: {', '.join(valid_model_types)}. "
                f"Auto mode has been removed to ensure explicit model selection."
            )
        
        if sr_model_type not in valid_model_types:
            raise ValueError(
                f"Invalid model_type: '{sr_model_type}'. "
                f"Must be one of: {', '.join(valid_model_types)}"
            )
        
        self.model_type = sr_model_type
        print(f"[Swin2SR.__init__] 最终 self.model_type: '{self.model_type}'")
        
        self.disabled = os.getenv("SWIN2SR_DISABLED", "false").lower() == "true"
        
        # Device configuration
        self.device = torch.device("cuda" if self.use_gpu and torch.cuda.is_available() else "cpu")
        
        # T4 优化：关闭 cudnn.benchmark（更稳定）
        if self.device.type == 'cuda':
            torch.backends.cudnn.benchmark = False
            print("[Swin2SR.__init__] Disabled cudnn.benchmark for T4 stability")
        
        self.models = {}  # Dict of models {scale: model}
        self.quantized_models = {}  # Dict of INT8 quantized models
        self.initialized = False
        
        # Check if disabled
        if self.disabled:
            print("[Swin2SR] Service disabled")
            self.initialized = True
            return
        
        # Initialize models
        self._init_local_model()
    
    def _init_local_model(self):
        """Initialize local model"""
        print("[Swin2SR] Initializing local model...")
        
        try:
            # Create model directory if not exists
            if not os.path.exists(self.model_path):
                os.makedirs(self.model_path, exist_ok=True)
                print(f"[Swin2SR] Created model directory: {self.model_path}")
            
            # Get cascade configuration
            cascade_scales = self.CASCADE_CONFIG.get(self.target_scale, [4])
            print(f"[Swin2SR] Target scale: X{self.target_scale}")
            print(f"[Swin2SR] Cascade configuration: X{'X'.join(map(str, cascade_scales))}")
            
            # Load models for each scale in cascade
            for scale in cascade_scales:
                if scale not in self.models:
                    self._load_single_model(scale)
            
            # Set self.model to first model for backward compatibility
            if len(self.models) > 0:
                first_scale = cascade_scales[0]
                self.model = self.models[first_scale]
                print(f"[Swin2SR] Set self.model to X{first_scale} model for backward compatibility")
            
            print(f"[Swin2SR] Initialization complete: {len(self.models)} models loaded, using device: {self.device}")
            self.initialized = True
            
            # T4 优化：INT8 量化在 Swin2SR 上有兼容性问题，暂时禁用
            # 参考：https://github.com/pytorch/pytorch/issues/58963
            # Swin Transformer 的复杂结构（窗口注意力、相对位置编码）与 INT8 动态量化不兼容
            if self.device.type == 'cuda' and torch.cuda.is_available():
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
                print(f"[Swin2SR] GPU memory: {gpu_memory:.1f}GB")
                
                # 使用 FP16 而不是 INT8
                if gpu_memory <= 16:
                    print(f"[Swin2SR] T4 detected, using FP16 mixed precision for optimal performance")
                    print(f"[Swin2SR] INT8 quantization disabled due to compatibility issues with Swin Transformer")
            
        except Exception as e:
            print(f"[Swin2SR] Initialization failed: {e}")
            print("[Swin2SR] Will use fallback mode")
    
    def _load_single_model(self, scale: int):
        """Load a single scale model"""
        print(f"\n[Swin2SR] ========== Loading X{scale} model ==========")
        
        # Check if already loaded
        if scale in self.models:
            print(f"[Swin2SR] Model X{scale} already loaded, skipping")
            return
        
        # Temporarily set self.scale
        old_scale = getattr(self, 'scale', None)
        self.scale = scale
        
        # Find model file
        model_file = self._find_model_file()
        
        # Restore original scale
        if old_scale is not None:
            self.scale = old_scale
        
        if not model_file:
            print(f"[Swin2SR] No model file found for X{scale}")
            return
        
        # Load model
        print(f"[Swin2SR] Loading model: {os.path.basename(model_file)}")
        
        try:
            # Import Swin2SR model
            import sys
            swin2sr_models_path = os.path.join(os.path.dirname(__file__), "..", "..", "swin2sr", "models")
            sys.path.append(swin2sr_models_path)
            from network_swin2sr import Swin2SR
            
            # Determine model type from filename
            model_filename = os.path.basename(model_file)
            print(f"[Swin2SR] Model filename: {model_filename}")
            
            # Create model based on type
            if "CompressedSR" in model_filename:
                print("[Swin2SR] Using CompressedSR model")
                img_size = 48
                model = Swin2SR(
                    upscale=scale,
                    in_chans=3,
                    img_size=img_size,
                    window_size=8,
                    img_range=1.0,
                    depths=[6, 6, 6, 6, 6, 6],
                    embed_dim=180,
                    num_heads=[6, 6, 6, 6, 6, 6],
                    mlp_ratio=2,
                    upsampler='pixelshuffle_aux',
                    resi_connection='1conv',
                    qkv_bias=True,
                    qk_scale=None,
                    drop_rate=0.,
                    attn_drop_rate=0.,
                    drop_path_rate=0.1,
                    norm_layer=torch.nn.LayerNorm,
                    ape=False,
                    patch_norm=True,
                    use_checkpoint=False
                )
                param_key = 'params'
            elif "ClassicalSR" in model_filename:
                print("[Swin2SR] Using ClassicalSR model")
                # Determine upsampler type based on scale
                # X2 uses pixelshuffle_aux, X4/X8 uses pixelshuffle
                upsampler_type = 'pixelshuffle_aux' if scale == 2 else 'pixelshuffle'
                print(f"[Swin2SR] Using upsampler: {upsampler_type} (scale={scale})")
                model = Swin2SR(
                    upscale=scale,
                    in_chans=3,
                    img_size=64,
                    window_size=8,
                    img_range=1.0,
                    depths=[6, 6, 6, 6, 6, 6],
                    embed_dim=180,
                    num_heads=[6, 6, 6, 6, 6, 6],
                    mlp_ratio=2,
                    upsampler=upsampler_type,
                    resi_connection='1conv',
                    qkv_bias=True,
                    qk_scale=None,
                    drop_rate=0.,
                    attn_drop_rate=0.,
                    drop_path_rate=0.1,
                    norm_layer=torch.nn.LayerNorm,
                    ape=False,
                    patch_norm=True,
                    use_checkpoint=False
                )
                param_key = 'params'
            elif "realworldsr" in model_filename.lower():
                print("[Swin2SR] Using RealWorldSR model")
                # RealWorldSR uses nearest+conv upsampler, not pixelshuffle
                model = Swin2SR(
                    upscale=scale,
                    in_chans=3,
                    img_size=64,
                    window_size=8,
                    img_range=1.0,
                    depths=[6, 6, 6, 6, 6, 6],
                    embed_dim=180,
                    num_heads=[6, 6, 6, 6, 6, 6],
                    mlp_ratio=2,
                    upsampler='nearest+conv',
                    resi_connection='1conv',
                    qkv_bias=True,
                    qk_scale=None,
                    drop_rate=0.,
                    attn_drop_rate=0.,
                    drop_path_rate=0.1,
                    norm_layer=torch.nn.LayerNorm,
                    ape=False,
                    patch_norm=True,
                    use_checkpoint=False
                )
                param_key = 'params'
            else:
                print("[Swin2SR] Using default model")
                model = Swin2SR(
                    upscale=scale,
                    in_chans=3,
                    img_size=64,
                    window_size=8,
                    img_range=1.0,
                    depths=[6, 6, 6, 6, 6, 6],
                    embed_dim=180,
                    num_heads=[6, 6, 6, 6, 6, 6],
                    mlp_ratio=2,
                    upsampler='pixelshuffle',
                    resi_connection='1conv',
                    qkv_bias=True,
                    qk_scale=None,
                    drop_rate=0.,
                    attn_drop_rate=0.,
                    drop_path_rate=0.1,
                    norm_layer=torch.nn.LayerNorm,
                    ape=False,
                    patch_norm=True,
                    use_checkpoint=False
                )
                param_key = 'params'
            
            # Load weights
            print(f"[Swin2SR] Loading weights from: {model_file}")
            checkpoint = torch.load(model_file, map_location=self.device)
            
            if param_key in checkpoint:
                print(f"[Swin2SR] Loading from '{param_key}' key")
                model.load_state_dict(checkpoint[param_key], strict=True)
            else:
                print("[Swin2SR] Key not found, loading directly")
                model.load_state_dict(checkpoint, strict=True)
            
            model.to(self.device)
            model.eval()
            
            # Save to models dict
            self.models[scale] = model
            
            print(f"[Swin2SR] Model X{scale} loaded successfully")
            
        except Exception as e:
            print(f"[Swin2SR] Failed to load model X{scale}: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _find_model_file(self) -> Optional[str]:
        """Find model file based on model_type and scale"""
        print(f"[Swin2SR] Model type: {self.model_type}")
        print(f"[Swin2SR] Model path: {self.model_path}")
        print(f"[Swin2SR] Scale: {self.scale}")
        
        # Search based on model_type
        if self.model_type == "compressed":
            # Search for CompressedSR model
            pattern = f"Swin2SR_CompressedSR_X{self.scale}_48.pth"
            model_file = os.path.join(self.model_path, pattern)
            print(f"[Swin2SR] Searching for CompressedSR: {pattern}")
            if os.path.exists(model_file):
                print(f"[Swin2SR] Found CompressedSR: {model_file}")
                return model_file
            else:
                raise FileNotFoundError(f"CompressedSR model not found: {pattern}")
        elif self.model_type == "classical":
            # Search for ClassicalSR model
            pattern = f"Swin2SR_ClassicalSR_X{self.scale}_64.pth"
            model_file = os.path.join(self.model_path, pattern)
            print(f"[Swin2SR] Searching for ClassicalSR: {pattern}")
            if os.path.exists(model_file):
                print(f"[Swin2SR] Found ClassicalSR: {model_file}")
                return model_file
            else:
                raise FileNotFoundError(f"ClassicalSR model not found: {pattern}")
        elif self.model_type == "realworld":
            # Search for RealWorldSR model
            patterns = [
                f"Swin2SR_RealworldSR_X{self.scale}_64_BSRGAN_PSNR.pth",  # BSRGAN
                f"Swin2SR_RealWorldSR_X{self.scale}_64.pth",  # RealWorld
            ]
            for pattern in patterns:
                model_file = os.path.join(self.model_path, pattern)
                print(f"[Swin2SR] Searching for RealWorldSR: {pattern}")
                if os.path.exists(model_file):
                    print(f"[Swin2SR] Found RealWorldSR: {model_file}")
                    return model_file
            raise FileNotFoundError(f"RealWorldSR model not found for scale X{self.scale}")
        
        # Should not reach here (model_type is validated in __init__)
        raise ValueError(f"Invalid model_type: {self.model_type}")
    
    def _load_model(self, model_file):
        """Load Swin2SR model from file"""
        try:
            # Import Swin2SR model
            import sys
            swin2sr_models_path = os.path.join(os.path.dirname(__file__), "..", "..", "swin2sr", "models")
            print(f"[Swin2SR] Swin2SR models path: {swin2sr_models_path}")
            sys.path.append(swin2sr_models_path)
            from network_swin2sr import Swin2SR
            
            # Determine model type from filename
            model_filename = os.path.basename(model_file)
            print(f"[Swin2SR] Model filename: {model_filename}")
            
            # Create model based on type
            if "CompressedSR" in model_filename:
                print("[Swin2SR] Using CompressedSR model")
                # CompressedSR uses smaller img_size
                img_size = 48  # Swin2SR_CompressedSR_X4_48.pth uses 48
                print(f"[Swin2SR] Using img_size={img_size}")
                
                model = Swin2SR(
                    upscale=self.scale,
                    in_chans=3,
                    img_size=img_size,
                    window_size=8,
                    img_range=1.0,
                    depths=[6, 6, 6, 6, 6, 6],
                    embed_dim=180,
                    num_heads=[6, 6, 6, 6, 6, 6],
                    mlp_ratio=2,
                    upsampler='pixelshuffle_aux',
                    resi_connection='1conv',
                    qkv_bias=True,
                    qk_scale=None,
                    drop_rate=0.,
                    attn_drop_rate=0.,
                    drop_path_rate=0.1,
                    norm_layer=torch.nn.LayerNorm,
                    ape=False,
                    patch_norm=True,
                    use_checkpoint=False
                )
                param_key = 'params'
            elif "ClassicalSR" in model_filename:
                print("[Swin2SR] Using ClassicalSR model")
                upsampler_type = 'pixelshuffle_aux' if self.scale == 2 else 'pixelshuffle'
                print(f"[Swin2SR] Using upsampler: {upsampler_type} (scale={self.scale})")
                
                model = Swin2SR(
                    upscale=self.scale,
                    in_chans=3,
                    img_size=64,
                    window_size=8,
                    img_range=1.0,
                    depths=[6, 6, 6, 6, 6, 6],
                    embed_dim=180,
                    num_heads=[6, 6, 6, 6, 6, 6],
                    mlp_ratio=2,
                    upsampler=upsampler_type,
                    resi_connection='1conv',
                    qkv_bias=True,
                    qk_scale=None,
                    drop_rate=0.,
                    attn_drop_rate=0.,
                    drop_path_rate=0.1,
                    norm_layer=torch.nn.LayerNorm,
                    ape=False,
                    patch_norm=True,
                    use_checkpoint=False
                )
                param_key = 'params'
            else:
                print("[Swin2SR] Using default model")
                model = Swin2SR(
                    upscale=self.scale,
                    in_chans=3,
                    img_size=64,
                    window_size=8,
                    img_range=1.0,
                    depths=[6, 6, 6, 6, 6, 6],
                    embed_dim=180,
                    num_heads=[6, 6, 6, 6, 6, 6],
                    mlp_ratio=2,
                    upsampler='pixelshuffle',
                    resi_connection='1conv',
                    qkv_bias=True,
                    qk_scale=None,
                    drop_rate=0.,
                    attn_drop_rate=0.,
                    drop_path_rate=0.1,
                    norm_layer=torch.nn.LayerNorm,
                    ape=False,
                    patch_norm=True,
                    use_checkpoint=False
                )
                param_key = 'params'
            
            # Load weights
            print(f"[Swin2SR] Loading weights from: {model_file}")
            checkpoint = torch.load(model_file, map_location=self.device)
            
            if param_key in checkpoint:
                print(f"[Swin2SR] Loading from '{param_key}' key")
                model.load_state_dict(checkpoint[param_key], strict=True)
            else:
                print("[Swin2SR] Key not found, loading directly")
                model.load_state_dict(checkpoint, strict=True)
            
            model.to(self.device)
            model.eval()
            
            print(f"[Swin2SR] Model loaded successfully")
            return model
            
        except Exception as e:
            print(f"[Swin2SR] Failed to load model: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def enhance(self, image: Image.Image) -> Tuple[Image.Image, Dict]:
        """
        Enhance image using super-resolution with T4 optimization (FP16 + INT8 + Tile)
        
        Args:
            image: PIL Image object
            
        Returns:
            Tuple of (enhanced_image, metadata)
        """
        start_time = time.time()
        original_size = image.size
        
        # Check if image is too large and needs tiling (T4 optimized thresholds)
        scale = self.target_scale
        
        # Calculate output dimensions
        output_w = original_size[0] * scale
        output_h = original_size[1] * scale
        
        # T4 优化的分块策略（参考 CSDN 教程）
        # 1. 输入 > 512px 就分块（避免中间特征图爆炸）
        # 2. 输出 > 2000px 就分块（避免显存尖峰）
        needs_tiling = (original_size[0] > self.max_input_dim or 
                       original_size[1] > self.max_input_dim or
                       output_w > self.max_output_dim or
                       output_h > self.max_output_dim)
        
        print(f"[Swin2SR.enhance] Original size: {original_size[0]}x{original_size[1]}")
        print(f"[Swin2SR.enhance] Output size: {output_w}x{output_h}")
        print(f"[Swin2SR.enhance] Target scale: X{scale}")
        print(f"[Swin2SR.enhance] Needs tiling: {needs_tiling}")
        
        if needs_tiling:
            print(f"[Swin2SR.enhance] Using tiling mode for large image processing")
            enhanced_image = self._enhance_tiled(image, scale)
            use_fp16_for_metadata = self.device.type == 'cuda' and torch.cuda.is_available()
        else:
            # Convert to numpy array
            img_array = np.array(image).astype(np.float32) / 255.0
            img_tensor = torch.from_numpy(img_array).permute(2, 0, 1).unsqueeze(0).to(self.device)
            
            # T4 优化：使用 FP16 混合精度
            use_fp16 = self.device.type == 'cuda' and torch.cuda.is_available()
            use_fp16_for_metadata = use_fp16
            
            if use_fp16:
                print(f"[Swin2SR.enhance] Using FP16 mixed precision for GPU acceleration")
            
            # Select model
            model = self.models.get(scale, self.model)
            
            # Apply super-resolution with FP16
            with torch.no_grad():
                if use_fp16:
                    # Enable automatic mixed precision (AMP) for faster inference
                    with torch.amp.autocast('cuda', dtype=torch.float16):
                        output = model(img_tensor)
                else:
                    output = model(img_tensor)
                
                # Swin2SR 模型返回可能是 dict 或 tuple，需要提取实际的 tensor
                if isinstance(output, dict):
                    enhanced_tensor = output.get('result', output.get('lr', img_tensor))
                elif isinstance(output, tuple):
                    enhanced_tensor = output[0]  # 取第一个元素
                else:
                    enhanced_tensor = output
            
            # Convert back to PIL Image
            enhanced_array = enhanced_tensor.squeeze(0).permute(1, 2, 0).cpu().numpy()
            enhanced_array = np.clip(enhanced_array * 255.0, 0, 255).astype(np.uint8)
            enhanced_image = Image.fromarray(enhanced_array)
        
        process_time = time.time() - start_time
        
        metadata = {
            "original_size": f"{original_size[0]}x{original_size[1]}",
            "enhanced_size": f"{enhanced_image.size[0]}x{enhanced_image.size[1]}",
            "scale_factor": self.target_scale,
            "process_time": process_time,
            "method": "swin2sr",
            "tiling_used": needs_tiling,
            "fp16_used": use_fp16_for_metadata,
            "int8_used": False
        }
        
        return enhanced_image, metadata
    
    def _enhance_tiled(self, image: Image.Image, scale: int) -> Image.Image:
        """
        Enhance large image using CSDN-recommended tiling approach (384x384 tiles + Gaussian blending)
        Reference: https://blog.csdn.net/weixin_42603332/article/details/157498845
        
        Args:
            image: PIL Image object
            scale: Target scale factor
            
        Returns:
            Enhanced PIL Image object
        """
        print(f"[Swin2SR._enhance_tiled] Starting CSDN-recommended tiled processing...")
        
        # CSDN 推荐参数
        tile_size = 384  # T4 最优平衡点
        tile_overlap = 32  # 32 像素重叠，避免块边界伪影
        
        print(f"[Swin2SR._enhance_tiled] Tile size: {tile_size}x{tile_size}, overlap: {tile_overlap}")
        
        # Check if FP16 is available
        use_fp16 = self.device.type == 'cuda' and torch.cuda.is_available()
        
        if use_fp16:
            print(f"[Swin2SR._enhance_tiled] Using FP16 mixed precision for tile processing")
        
        # Select model
        model = self.models.get(scale, self.model)
        
        # Convert to numpy
        img_array = np.array(image).astype(np.float32) / 255.0
        h, w = img_array.shape[:2]
        
        # CSDN 关键：先对图像进行 padding，确保能被 tile_size 整除
        pad_h = (tile_size - h % tile_size) % tile_size
        pad_w = (tile_size - w % tile_size) % tile_size
        
        if pad_h > 0 or pad_w > 0:
            print(f"[Swin2SR._enhance_tiled] Padding image: {h}x{w} -> {h+pad_h}x{w+pad_w}")
            img_padded = np.pad(img_array, ((0, pad_h), (0, pad_w), (0, 0)), mode='reflect')
        else:
            img_padded = img_array
        
        h_padded, w_padded = img_padded.shape[:2]
        
        # Create output array
        output_h = h_padded * scale
        output_w = w_padded * scale
        output_array = np.zeros((output_h, output_w, 3), dtype=np.float32)
        weight_array = np.zeros((output_h, output_w, 1), dtype=np.float32)
        
        # CSDN 关键：创建线性加权掩码（简单易懂）
        def create_linear_weight_mask(tile_h, tile_w):
            """
            创建线性权重掩码，中心权重 1.0，边缘线性衰减到 0
            比高斯加权更简单、更直观
            """
            # 创建归一化坐标 [-1, 1]
            y = np.linspace(-1, 1, tile_h * scale)
            x = np.linspace(-1, 1, tile_w * scale)
            yy, xx = np.meshgrid(y, x, indexing='ij')
            
            # 线性权重：距离中心越远，权重越低
            # 使用 (1 - |x|) * (1 - |y|) 实现线性衰减
            mask = (1 - np.abs(xx)) * (1 - np.abs(yy))
            
            # 确保最小值不为 0（避免完全黑色）
            mask = np.maximum(mask, 0.1)
            
            return mask[:, :, np.newaxis].astype(np.float32)
        
        # CSDN 关键：计算步长和总 tile 数
        step = tile_size - tile_overlap
        tiles_y = (h_padded - tile_overlap + step - 1) // step
        tiles_x = (w_padded - tile_overlap + step - 1) // step
        total_tiles = tiles_y * tiles_x
        
        print(f"[Swin2SR._enhance_tiled] Grid: {tiles_y}x{tiles_x} = {total_tiles} tiles")
        
        # Process tiles
        tile_count = 0
        
        for ty in range(tiles_y):
            for tx in range(tiles_x):
                tile_count += 1
                
                # CSDN 关键：计算 tile 在原始图像中的位置（带重叠）
                y_start = ty * step
                y_end = min(h_padded, y_start + tile_size)
                x_start = tx * step
                x_end = min(w_padded, x_start + tile_size)
                
                # 确保 tile 尺寸一致（用于高斯掩码）
                actual_h = y_end - y_start
                actual_w = x_end - x_start
                
                print(f"[Swin2SR._enhance_tiled] Processing tile {tile_count}/{total_tiles} at ({x_start}, {y_start}) size {actual_w}x{actual_h}")
                
                # Extract tile
                tile = img_padded[y_start:y_end, x_start:x_end]
                
                # Convert to tensor
                tile_tensor = torch.from_numpy(tile).permute(2, 0, 1).unsqueeze(0).to(self.device)
                
                # Apply super-resolution with FP16
                with torch.no_grad():
                    if use_fp16:
                        with torch.amp.autocast('cuda', dtype=torch.float16):
                            output = model(tile_tensor)
                    else:
                        output = model(tile_tensor)
                    
                    if isinstance(output, dict):
                        enhanced_tile = output.get('result', output.get('lr', tile_tensor))
                    elif isinstance(output, tuple):
                        enhanced_tile = output[0]
                    else:
                        enhanced_tile = output
                
                # Convert back to numpy
                enhanced_tile = enhanced_tile.squeeze(0).permute(1, 2, 0).cpu().numpy()
                enhanced_tile = np.clip(enhanced_tile * 255.0, 0, 255).astype(np.float32)
                
                # Calculate output positions
                out_y_start = y_start * scale
                out_y_end = y_end * scale
                out_x_start = x_start * scale
                out_x_end = x_end * scale
                
                # CSDN 关键：创建线性权重掩码并融合
                weight_mask = create_linear_weight_mask(actual_h, actual_w)
                
                # Blend tile into output with weighted averaging
                output_array[out_y_start:out_y_end, out_x_start:out_x_end] += enhanced_tile * weight_mask
                weight_array[out_y_start:out_y_end, out_x_start:out_x_end] += weight_mask
        
        # CSDN 关键：归一化（避免 division by zero）
        weight_array = np.maximum(weight_array, 1e-6)
        output_array = output_array / weight_array
        
        # Convert to uint8
        output_array = np.clip(output_array, 0, 255).astype(np.uint8)
        
        # CSDN 关键：裁剪掉 padding 区域
        if pad_h > 0 or pad_w > 0:
            crop_h = h * scale
            crop_w = w * scale
            print(f"[Swin2SR._enhance_tiled] Cropping output: {output_h}x{output_w} -> {crop_h}x{crop_w}")
            output_array = output_array[:crop_h, :crop_w, :]
        
        # Convert to PIL Image
        enhanced_image = Image.fromarray(output_array)
        
        print(f"[Swin2SR._enhance_tiled] Tiled processing complete. Output size: {enhanced_image.size[0]}x{enhanced_image.size[1]}")
        
        return enhanced_image
    
    def enhance_bytes(self, image_bytes: bytes, enable_text_optimization: bool = False) -> Tuple[bytes, Dict]:
        """
        Enhance image from bytes
        
        Args:
            image_bytes: Image bytes
            enable_text_optimization: Whether to enable text optimization
            
        Returns:
            Tuple of (enhanced_image_bytes, metadata)
        """
        # Load image from bytes
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        # Enhance image
        enhanced_image, metadata = self.enhance(image)
        
        # Apply text optimization if enabled
        if enable_text_optimization:
            from .image_enhancer import optimize_for_text
            # Convert enhanced image to bytes
            temp_output = io.BytesIO()
            enhanced_image.save(temp_output, format="PNG")
            temp_output.seek(0)
            # Apply text optimization
            optimized_bytes = optimize_for_text(temp_output.getvalue())
            # Load optimized image
            enhanced_image = Image.open(io.BytesIO(optimized_bytes))
            metadata['text_optimized'] = True
            # 更新尺寸信息（文字优化可能会改变尺寸）
            metadata['enhanced_size'] = f"{enhanced_image.size[0]}x{enhanced_image.size[1]}"
        
        # Convert to bytes
        output = io.BytesIO()
        enhanced_image.save(output, format="PNG")
        enhanced_bytes = output.getvalue()
        
        return enhanced_bytes, metadata


# Global service instances cache (key: model_type, value: Swin2SRService)
_service_cache: Dict[str, Swin2SRService] = {}


def get_sr_service(sr_model_type: str, target_scale: int = 4) -> Swin2SRService:
    """Get or create Swin2SR service instance for specific model_type"""
    cache_key = f"{sr_model_type}_x{target_scale}"
    if cache_key not in _service_cache:
        _service_cache[cache_key] = Swin2SRService(sr_model_type=sr_model_type, target_scale=target_scale)
    return _service_cache[cache_key]


def enhance_image(image_bytes: bytes, sr_model_type: str = "auto", target_scale: int = 4, enable_text_optimization: bool = False) -> Tuple[bytes, Dict]:
    """
    Enhance image using super-resolution
    
    Args:
        image_bytes: Input image bytes
        sr_model_type: Model type to use
        target_scale: Target scale factor
        enable_text_optimization: Whether to enable text optimization
        
    Returns:
        Tuple of (enhanced_image_bytes, metadata)
    """
    service = get_sr_service(sr_model_type=sr_model_type, target_scale=target_scale)
    return service.enhance_bytes(image_bytes, enable_text_optimization=enable_text_optimization)


# 注意：不再在此文件中预加载模型
# 模型预加载已在 app/main.py 的 startup 事件中统一处理
# 避免重复加载，浪费启动时间和内存
