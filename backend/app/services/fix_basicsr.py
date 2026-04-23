#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复 basicsr 与 torchvision 0.17.0+ 的兼容性问题
"""

import sys
from unittest.mock import MagicMock

# 在导入 basicsr 之前，先创建兼容层
try:
    from torchvision.transforms.functional import rgb_to_grayscale
    
    # 创建一个模拟模块
    functional_tensor_mock = MagicMock()
    functional_tensor_mock.rgb_to_grayscale = rgb_to_grayscale
    
    # 注册到 sys.modules
    sys.modules['torchvision.transforms.functional_tensor'] = functional_tensor_mock
    
    print("[OK] 已修复 basicsr 与 torchvision 0.17.0+ 的兼容性问题")
    
except ImportError as e:
    print(f"[WARN] 修复失败: {e}")
