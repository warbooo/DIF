"""
修复 PaddleOCR 3.0+ 与 PaddlePaddle 3.0+ 的兼容性问题
修复：AttributeError: 'paddle.base.libpaddle.AnalysisConfig' object has no attribute 'set_optimization_level'
修复：NotImplementedError: ConvertPirAttribute2RuntimeAttribute not support
修复：Paddle 和 PyTorch CUDA 冲突问题
"""
import os

# 首先禁用 MKLDNN，避免兼容性问题
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['MKLDNN_VERBOSE'] = '0'
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'

# 修复 Paddle 和 PyTorch CUDA 冲突
# 让 Paddle 使用不同的 CUDA 初始化方式
os.environ['PADDLE_CUDA_USE_DEVICE_BUFFER_ALLOCATOR'] = '0'
os.environ['PADDLE_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'

def fix_paddle_analysis_config():
    """
    修复 AnalysisConfig 的兼容性问题
    """
    try:
        import paddle
        from paddle import base as paddle_base
        
        # 检查 AnalysisConfig 是否存在
        if hasattr(paddle_base.libpaddle, 'AnalysisConfig'):
            AnalysisConfig = paddle_base.libpaddle.AnalysisConfig
            
            # 给 AnalysisConfig 添加一个空的 set_optimization_level 方法
            if not hasattr(AnalysisConfig, 'set_optimization_level'):
                def dummy_set_optimization_level(self, level):
                    print(f"[WARN]  [PaddleOCR 补丁] 忽略 set_optimization_level({level}) 调用")
                
                AnalysisConfig.set_optimization_level = dummy_set_optimization_level
                print("[OK]  [PaddleOCR 补丁] 已添加 set_optimization_level 兼容性方法")
            
            # 禁用 MKLDNN
            if hasattr(AnalysisConfig, 'disable_mkldnn'):
                original_init = AnalysisConfig.__init__
                def new_init(self, *args, **kwargs):
                    original_init(self, *args, **kwargs)
                    self.disable_mkldnn()
                    print("[OK]  [PaddleOCR 补丁] 已禁用 MKLDNN")
                AnalysisConfig.__init__ = new_init
        
        # 也尝试修复 paddle.inference.Config
        try:
            from paddle.inference import Config
            if not hasattr(Config, 'set_optimization_level'):
                def dummy_set_optimization_level(self, level):
                    print(f"[WARN]  [PaddleOCR 补丁] 忽略 Config.set_optimization_level({level}) 调用")
                
                Config.set_optimization_level = dummy_set_optimization_level
                print("[OK]  [PaddleOCR 补丁] 已添加 Config.set_optimization_level 兼容性方法")
            
            # 禁用 MKLDNN
            if hasattr(Config, 'disable_mkldnn'):
                original_init = Config.__init__
                def new_init_config(self, *args, **kwargs):
                    original_init(self, *args, **kwargs)
                    self.disable_mkldnn()
                    print("[OK]  [PaddleOCR 补丁] 已禁用 Config MKLDNN")
                Config.__init__ = new_init_config
        except ImportError:
            pass
            
    except Exception as e:
        print(f"[WARN]  [PaddleOCR 补丁] 应用补丁时出错: {e}")
        import traceback
        traceback.print_exc()


# 在模块导入时自动应用补丁
fix_paddle_analysis_config()
