#!/usr/bin/env python3
"""
RapidOCR v5 服务脚本
使用 ONNXRuntime GPU 加速，基于 PaddleOCR v5 的 ONNX 模型

功能：
- 接收 base64 编码的图像数据
- 执行 OCR 识别
- 返回识别结果（文本和置信度）
- 支持 GPU 加速
"""
import sys
import json
import base64
from io import BytesIO
from rapidocr_onnxruntime import RapidOCR


def main():
    """主函数"""
    print("[RapidOCR Service] 初始化 RapidOCR 引擎...")
    
    # 初始化 RapidOCR 引擎
    # 根据RapidOCR官方文档参数调优指南进行优化
    # 参考：https://blog.csdn.net/gitblog_00157/article/details/154628057
    ocr = RapidOCR(
        # 全局参数
        text_score=0.3,  # 降低置信度阈值，保留更多候选文本（默认0.5）
        
        # 文本检测参数（Det模块）
        det_use_gpu=True,
        det_limit_side_len=1024,  # 增加图像长边限制，提高大图像检测能力（默认736）
        det_db_thresh=0.2,  # 降低二值化阈值，提高低对比度图像检测效果（默认0.3）
        det_db_box_thresh=0.3,  # 降低框阈值，减少漏检
        det_unclip_ratio=1.8,  # 增加膨胀系数，确保文本框更宽松（默认1.6）
        
        # 文本识别参数（Rec模块）
        rec_use_gpu=True,
        rec_batch_num=16,  # 增大批处理大小，GPU环境下提高吞吐量（默认6）
        rec_img_shape=[3, 48, 640],  # 增大识别图像宽度，适合长文本识别（默认[3,48,320]）
        
        # 方向分类参数
        cls_use_gpu=True,
    )
    
    print("引擎初始化完成")
    import sys
    sys.stdout.flush()
    
    # 处理输入请求
    while True:
        try:
            # 读取一行输入
            line = sys.stdin.readline()
            if not line:
                break
            
            # 解析请求
            request = json.loads(line.strip())
            image_base64 = request.get('image')
            enable_spell_correction = request.get('enable_spell_correction', False)
            
            if not image_base64:
                response = {
                    'success': False,
                    'text': '',
                    'confidences': [],
                    'message': '缺少图像数据'
                }
                print(json.dumps(response))
                continue
            
            # 解码 base64 图像
            image_bytes = base64.b64decode(image_base64)
            # 直接使用bytes作为输入，而不是BytesIO
            result, elapse = ocr(image_bytes)
            
            if result:
                # 提取文本和置信度
                text_lines = []
                confidences = []
                
                for line in result:
                    text = line[1]
                    confidence = line[2]
                    text_lines.append(text)
                    confidences.append(float(confidence))
                
                # 构建响应
                response = {
                    'success': True,
                    'text': '\n'.join(text_lines),
                    'confidences': confidences,
                    'message': '识别成功',
                    'elapse': elapse
                }
            else:
                # 未识别到文本
                response = {
                    'success': True,
                    'text': '',
                    'confidences': [],
                    'message': '未识别到文本',
                    'elapse': elapse
                }
            
            # 输出响应
            print(json.dumps(response))
            sys.stdout.flush()
            
        except Exception as e:
            # 处理异常
            response = {
                'success': False,
                'text': '',
                'confidences': [],
                'message': f'处理错误: {str(e)}'
            }
            print(json.dumps(response))
            sys.stdout.flush()


if __name__ == '__main__':
    main()
