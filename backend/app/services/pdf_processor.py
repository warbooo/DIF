"""
PDF文件处理模块
将PDF转换为图像，支持多页PDF处理
"""
import io
from PIL import Image
from typing import List, Tuple, Optional
import base64


class PDFProcessor:
    """PDF处理器"""
    
    def __init__(self):
        self.available = False
        self.pdf2image_available = False
        self.pypdf_available = False
        
        # 检查依赖库
        self._check_dependencies()
    
    def _check_dependencies(self):
        """检查依赖库是否可用"""
        try:
            from pdf2image import convert_from_bytes
            self.pdf2image_available = True
            self.available = True
            print("[PDF Processor] pdf2image 可用")
        except ImportError:
            print("[PDF Processor] pdf2image 未安装，将尝试使用其他方法")
        
        try:
            import pypdf
            self.pypdf_available = True
            print("[PDF Processor] pypdf 可用")
        except ImportError:
            print("[PDF Processor] pypdf 未安装")
    
    def is_pdf(self, filename: str) -> bool:
        """检查是否为PDF文件"""
        return filename.lower().endswith('.pdf')
    
    def pdf_to_images(self, pdf_bytes: bytes, dpi: int = 200, 
                      first_page: int = None, last_page: int = None) -> List[Image.Image]:
        """
        将PDF转换为图像列表
        
        Args:
            pdf_bytes: PDF文件字节
            dpi: 分辨率（DPI）
            first_page: 起始页码（从1开始）
            last_page: 结束页码
        
        Returns:
            PIL图像列表
        """
        if not self.pdf2image_available:
            raise ImportError("pdf2image 未安装，请安装: pip install pdf2image")
        
        from pdf2image import convert_from_bytes
        
        print(f"[PDF Processor] 正在转换PDF，DPI: {dpi}")
        
        # 转换参数
        kwargs = {
            'dpi': dpi,
            'fmt': 'png',
            'thread_count': 4,
        }
        
        if first_page is not None:
            kwargs['first_page'] = first_page
        if last_page is not None:
            kwargs['last_page'] = last_page
        
        # 执行转换
        images = convert_from_bytes(pdf_bytes, **kwargs)
        
        print(f"[PDF Processor] PDF转换完成，共 {len(images)} 页")
        return images
    
    def pdf_to_single_image(self, pdf_bytes: bytes, dpi: int = 200, 
                            page: int = 1) -> Optional[Image.Image]:
        """
        将PDF的某一页转换为单张图像
        
        Args:
            pdf_bytes: PDF文件字节
            dpi: 分辨率（DPI）
            page: 页码（从1开始）
        
        Returns:
            PIL图像
        """
        images = self.pdf_to_images(pdf_bytes, dpi=dpi, first_page=page, last_page=page)
        if images:
            return images[0]
        return None
    
    def get_pdf_info(self, pdf_bytes: bytes) -> dict:
        """
        获取PDF信息
        
        Args:
            pdf_bytes: PDF文件字节
        
        Returns:
            包含PDF信息的字典
        """
        info = {
            'page_count': 0,
            'has_text': False,
            'metadata': {}
        }
        
        if self.pypdf_available:
            try:
                from pypdf import PdfReader
                
                reader = PdfReader(io.BytesIO(pdf_bytes))
                info['page_count'] = len(reader.pages)
                
                # 尝试读取第一页文本
                if len(reader.pages) > 0:
                    try:
                        text = reader.pages[0].extract_text()
                        info['has_text'] = len(text.strip()) > 0
                    except:
                        pass
                
                # 读取元数据
                if reader.metadata:
                    info['metadata'] = {
                        'title': reader.metadata.title or '',
                        'author': reader.metadata.author or '',
                        'subject': reader.metadata.subject or '',
                        'creator': reader.metadata.creator or '',
                    }
            
            except Exception as e:
                print(f"[PDF Processor] 读取PDF信息失败: {e}")
        
        return info
    
    def image_to_base64(self, image: Image.Image) -> str:
        """将图像转换为base64"""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def process_pdf_for_ocr(self, pdf_bytes: bytes, filename: str, 
                            page: int = 1, dpi: int = 300) -> Tuple[bytes, dict]:
        """
        处理PDF用于OCR识别
        
        Args:
            pdf_bytes: PDF文件字节
            filename: 文件名
            page: 页码
            dpi: 分辨率
        
        Returns:
            (图像字节, 处理信息)
        """
        info = self.get_pdf_info(pdf_bytes)
        
        # 转换为图像
        image = self.pdf_to_single_image(pdf_bytes, dpi=dpi, page=page)
        
        if image is None:
            raise Exception("PDF转换失败")
        
        # 转换为字节
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()
        
        return image_bytes, {
            'original_filename': filename,
            'page': page,
            'total_pages': info.get('page_count', 1),
            'dpi': dpi,
            'image_size': f"{image.width}x{image.height}",
        }


# 全局PDF处理器实例
_pdf_processor: Optional[PDFProcessor] = None


def get_pdf_processor() -> PDFProcessor:
    """获取全局PDF处理器实例"""
    global _pdf_processor
    if _pdf_processor is None:
        _pdf_processor = PDFProcessor()
    return _pdf_processor


def is_pdf_file(filename: str) -> bool:
    """检查是否为PDF文件"""
    processor = get_pdf_processor()
    return processor.is_pdf(filename)


def process_pdf(pdf_bytes: bytes, filename: str, page: int = 1) -> Tuple[bytes, dict]:
    """
    处理PDF文件的便捷函数
    
    Args:
        pdf_bytes: PDF文件字节
        filename: 文件名
        page: 页码
    
    Returns:
        (图像字节, 处理信息)
    """
    processor = get_pdf_processor()
    return processor.process_pdf_for_ocr(pdf_bytes, filename, page)
