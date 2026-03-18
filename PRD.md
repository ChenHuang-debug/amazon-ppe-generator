# Coze 亚马逊PPE产品主图生成工作流 - 完整配置手册

## 📋 工作流总体结构

```
[开始节点] 
    ↓ (用户输入产品信息+白底图片)
[LLM节点1：产品特征分析]
    ↓ (JSON输出产品分析结果)
[LLM节点2：生成7组提示词]
    ↓ (JSON输出7张图的提示词)
[代码节点：解析JSON提取提示词]
    ↓ (提取出prompt_1 ~ prompt_7)
[并行节点组]
  ├── [图生图节点1] ← 参考图+prompt_1
  ├── [图生图节点2] ← 参考图+prompt_2
  ├── [图生图节点3] ← 参考图+prompt_3
  ├── [图生图节点4] ← 参考图+prompt_4
  ├── [图生图节点5] ← 参考图+prompt_5
  ├── [图生图节点6] ← 参考图+prompt_6
  └── [图生图节点7] ← 参考图+prompt_7
    ↓ (7张图片URL)
[LLM节点3：生成使用说明和建议]
    ↓ (中文说明文案)
[结束节点]
    ↓ (输出7张图+说明)
```

---

## 第一步：创建工作流

1. 登录 [Coze平台](https://www.coze.com) 或 [Coze国内版](https://www.coze.cn)
2. 点击左侧「**工作流**」
3. 点击「**+ 创建工作流**」
4. 填写信息：
   - **工作流名称**：`Amazon PPE Product Image Generator`（或中文：`亚马逊PPE产品主图生成器`）
   - **描述**：`一键生成7张符合亚马逊规范的PPE产品主图`
   - **选择创建方式**：`从空白创建`
5. 点击「**创建**」

现在你进入了工作流编辑界面，左边是节点库，中间是编辑区，右边是节点配置面板。

---

## 第二步：节点一 - 开始节点（Start）

### 2.1 添加开始节点
节点库已自动添加了「开始」节点，点击它打开右侧配置面板。

### 2.2 配置输入变量

点击右侧面板中的「**添加变量**」按钮，逐个添加以下11个变量：

#### 第1个变量：product_name
```
变量名：product_name
中文标签：产品名称（英文）
变量类型：String
是否必填：是 ✅
默认值：（留空）
说明：如 High Visibility Reflective Safety Vest
```

#### 第2个变量：product_category
```
变量名：product_category
中文标签：产品类别
变量类型：String
是否必填：是 ✅
默认值：（留空）
说明：vest / raincoat / rain_pants / cap_cover
```

#### 第3个变量：product_color
```
变量名：product_color
中文标签：主色调
变量类型：String
是否必填：是 ✅
默认值：（留空）
说明：Yellow / Orange / Lime Green 等颜色名称
```

#### 第4个变量：reflective_type
```
变量名：reflective_type
中文标签：反光条类型
变量类型：String
是否必填：是 ✅
默认值：（留空）
说明：2-inch silver strips / segmented tape 等
```

#### 第5个变量：certifications
```
变量名：certifications
中文标签：安全认证
变量类型：String
是否必填：是 ✅
默认值：（留空）
说明：ANSI/ISEA 107 Class 2 或 Class 3 等
```

#### 第6个变量：key_features
```
变量名：key_features
中文标签：核心功能特性
变量类型：String
是否必填：是 ✅
默认值：（留空）
说明：6 pockets, zipper, adjustable waist 等，用逗号分隔
```

#### 第7个变量：target_scene
```
变量名：target_scene
中文标签：使用场景
变量类型：String
是否必填：是 ✅
默认值：（留空）
说明：construction, road work, warehouse 等
```

#### 第8个变量：price_point
```
变量名：price_point
中文标签：价格定位
变量类型：String
是否必填：否
默认值：（留空）
说明：budget / mid-range / premium
```

#### 第9个变量：product_material
```
变量名：product_material
中文标签：产品材质
变量类型：String
是否必填：否
默认值：（留空）
说明：polyester, 100% polyester, mesh 等
```

#### 第10个变量：product_image
```
变量名：product_image
中文标签：产品参考图（白底）
变量类型：File / Image
是否必填：是 ✅
默认值：（留空）
说明：上传白底产品原图，作为图生图参考
```

#### 第11个变量：target_asin（可选）
```
变量名：target_asin
中文标签：竞品ASIN（参考）
变量类型：String
是否必填：否
默认值：（留空）
说明：参考竞品的ASIN，可留空
```

**完成后的开始节点样子：**
```
输入变量（11个）
├── product_name ✅
├── product_category ✅
├── product_color ✅
├── reflective_type ✅
├── certifications ✅
├── key_features ✅
├── target_scene ✅
├── price_point
├── product_material
├── product_image ✅
└── target_asin
```

保存后点击右上角「**完成**」，回到编辑区。

---

## 第三步：节点二 - LLM节点1（产品特征分析）

### 3.1 添加LLM节点
在编辑区中间，右键 → 选择「**添加节点**」→ 搜索「LLM」→ 点击「**LLM**」

### 3.2 配置节点基础信息

**节点名称**：`产品特征分析`

**模型选择**：
- 国际版Coze推荐：**GPT-4o**
- 国内版Coze推荐：**Claude 3.5 Sonnet** 或 **ChatGPT-4o**
- 备选：**GLM-4** (智谱清言)

**参数设置**：
```
Temperature（温度）：0.3
Max Tokens（最大Token）：2000
```

### 3.3 配置System Prompt

点击「System」输入框，复制粘贴以下内容：

```
你是亚马逊PPE产品（个人防护装备）视觉营销和选品专家，拥有10年以上电商运营经验。

你深度理解：
1. 亚马逊主图规则：纯白背景RGB(255,255,255)、产品占比85%以上、无水印、最小1000×1000px、第一张必须实物图
2. PPE买家心理：安全认证优先级最高、视觉品质体现耐用性、竞品差异化是转化关键
3. 反光背心/雨衣/罩裤等PPE产品的视觉卖点
4. 高转化率产品图的构图原则和配色搭配

你的分析务必精准、专业、逻辑清晰，便于后续AI生图。
```

### 3.4 配置User Prompt

点击「User」输入框，复制粘贴以下内容：

```
请分析以下PPE产品信息，为生成7张高转化率亚马逊主图做准备：

【产品基本信息】
- 产品名称：{{start.product_name}}
- 产品类别：{{start.product_category}}
- 主色调：{{start.product_color}}
- 反光条类型：{{start.reflective_type}}
- 安全认证：{{start.certifications}}
- 核心功能：{{start.key_features}}
- 使用场景：{{start.target_scene}}
- 价格定位：{{start.price_point}}
- 产品材质：{{start.product_material}}

请按以下JSON格式输出分析结果，只输出JSON，不要任何其他文字：

{
  "product_summary": "产品核心卖点总结（一句话）",
  "primary_buyer_persona": "主要买家画像描述（2-3句）",
  "key_pain_points": ["买家痛点1", "痛点2", "痛点3"],
  "unique_selling_points": ["卖点1", "卖点2", "卖点3", "卖点4", "卖点5"],
  "visual_differentiation": "相比竞品如何在视觉上差异化",
  "color_description_for_image": "精确的英文颜色描述，用于AI生图",
  "material_and_texture_description": "材质质感描述，突出品质感",
  "recommended_lighting_style": "推荐打光方式（studio softbox / natural light等）",
  "must_show_features": ["必须展示的功能1", "功能2", "功能3"],
  "background_requirements": "背景要求（必须纯白）",
  "7_image_strategy": {
    "image_1_hero": "正面主图策略：展示整体正面，产品居中，85%占比",
    "image_2_reflective_detail": "反光条细节：特写反光条的质感和反射效果",
    "image_3_back_view": "背面展示：展示背部反光条和整体廓形",
    "image_4_flat_lay": "平铺功能：展示所有功能区域（口袋、拉链、调节带等）",
    "image_5_three_quarter": "45度角立体：展示产品立体感和蓬松度",
    "image_6_feature_closeup": "功能特写：选择一个主要功能部件（如反光条/拉链/调节系统）特写",
    "image_7_hanging": "悬挂展示：衣架上悬挂，展示整体廓形，看起来蓬松、有质感"
  }
}

分析要点：
- 色彩描述要用英文（便于后续提示词生成）
- 7张图的策略要具体可执行
- 优先考虑ANSI认证等安全要素的视觉体现
```

### 3.5 配置输出变量

右侧面板下方，点击「**添加输出**」：

```
输出变量名：analysis_result
变量类型：String
说明：LLM返回的完整JSON分析结果
```

点击「**完成**」保存这个LLM节点。

---

## 第四步：节点三 - LLM节点2（生成7组提示词）

### 4.1 添加第二个LLM节点

右键 → 「**添加节点**」→ 搜索「LLM」→ 点击「**LLM**」

### 4.2 配置基础信息

**节点名称**：`生成图像提示词`

**模型选择**：**GPT-4o**（英文提示词生成能力最强）

**参数**：
```
Temperature：0.4
Max Tokens：4500
```

### 4.3 配置System Prompt

```
你是专业的AI图像提示词工程师，专注于电商产品图生成。你精通：
- DALL-E 3、Stable Diffusion、Flux等模型的提示词格式
- 亚马逊主图规范和限制
- 基于参考图片的图生图（Image-to-Image）提示词优化

你生成的提示词需要满足以下条件：
1. 全部使用英文
2. 符合亚马逊主图规范：纯白背景、无文字无水印、产品占比85%以上
3. 提示词以 "Based on the reference product image, " 开头
4. 描述背景、角度、光线的变化，保持产品原有特征
5. 包含正向提示词（positive）和负向提示词（negative）
6. 每张图突出不同卖点，避免重复

亚马逊主图铁律（每张都必须体现）：
- pure white background, RGB(255,255,255), completely white
- no text, no watermark, no logo, no human
- product occupies at least 85% of frame
- professional product photography, studio lighting
- high resolution, 8K quality, photorealistic
```

### 4.4 配置User Prompt

```
基于以下产品分析：
{{step_3.analysis_result}}

产品信息：
- 产品：{{start.product_name}}
- 类别：{{start.product_category}}
- 颜色：{{start.product_color}}
- 认证：{{start.certifications}}

生成7张亚马逊主图的英文提示词，严格按以下JSON格式输出，只输出JSON不要其他文字：

{
  "images": [
    {
      "index": 1,
      "name": "Hero Shot - Front View",
      "purpose": "正面主图，展示整体正面，这是第一主图最重要",
      "composition_notes": "产品正面向前，居中，占图片85%，头部和脚部各留一点空间",
      "positive_prompt": "Based on the reference product image, professional product photography of high visibility {{start.product_color}} {{start.product_category}}, front view, centered composition, {{start.reflective_type}} visible, pure white background RGB(255,255,255), studio lighting with soft shadows, professional e-commerce photography, detailed and sharp, 8K resolution, photorealistic, no human",
      "negative_prompt": "text, watermark, logo, background, person, shadow, blur, low quality, distorted, poor lighting, dark background"
    },
    {
      "index": 2,
      "name": "Reflective Strip Detail",
      "purpose": "反光条细节，展示反光条的质感和反射效果，体现安全认证",
      "composition_notes": "反光条特写，占图片60%，展示反光条的反射光泽和细节纹理",
      "positive_prompt": "Based on the reference product image, close-up detailed shot of reflective strips on {{start.product_color}} {{start.product_category}}, macro photography, showing reflective tape texture and silver shine, {{start.certifications}} compliance visible, pure white background, professional product photography, high detail, 8K resolution, sharp focus on reflective material",
      "negative_prompt": "text, watermark, full product, person, blurry, low quality, dark, distorted reflection"
    },
    {
      "index": 3,
      "name": "Back View",
      "purpose": "背面展示，展示背部完整外观和反光条位置",
      "composition_notes": "产品背面向前，居中，85%占比，展示背部的反光条布局",
      "positive_prompt": "Based on the reference product image, professional product photography of {{start.product_color}} {{start.product_category}} from back view, centered composition, back reflective strips clearly visible, pure white background RGB(255,255,255), studio lighting, detailed, professional e-commerce photo, 8K resolution, photorealistic, no human",
      "negative_prompt": "text, watermark, front view, person, shadow, blur, background, low quality, distorted"
    },
    {
      "index": 4,
      "name": "Feature Flat Lay",
      "purpose": "平铺展示，展示所有功能部件（口袋、拉链、调节带等）",
      "composition_notes": "产品平铺展开，所有功能区域清晰可见，对称布局",
      "positive_prompt": "Based on the reference product image, flat lay product photography of {{start.product_color}} {{start.product_category}} showing all features: {{start.key_features}}, pure white background, top-down view, professional product photography, all details visible, sharp focus, 8K resolution, studio lighting, e-commerce style photography",
      "negative_prompt": "text, watermark, person, hanging, 3D view, shadow, wrinkled, blurry, low quality, background"
    },
    {
      "index": 5,
      "name": "Three-Quarter Angle",
      "purpose": "45度角立体展示，展现产品的立体感和蓬松度",
      "composition_notes": "产品45度角展示，展现立体感，居中构图，85%占比",
      "positive_prompt": "Based on the reference product image, professional product photography of {{start.product_color}} {{start.product_category}} from three-quarter angle (45 degrees), showing 3D form and volume, pure white background RGB(255,255,255), centered composition, product occupies 85% of frame, studio lighting, high detail, 8K resolution, professional e-commerce photography",
      "negative_prompt": "text, watermark, flat view, person, background objects, shadow, blur, distorted, poor quality"
    },
    {
      "index": 6,
      "name": "Function Close-up Detail",
      "purpose": "功能特写，选择产品最重要的一个功能部件特写展示",
      "composition_notes": "产品关键功能部件（如反光条、拉链、口袋或调节带）特写，展示品质和细节",
      "positive_prompt": "Based on the reference product image, macro close-up shot of {{start.product_category}} key feature {{start.key_features}}, showing texture and quality, pure white background, professional product photography, sharp detailed focus, 8K resolution, studio lighting, premium quality appearance",
      "negative_prompt": "text, watermark, full product, person, blurry, low quality, dark background, distorted, wrinkled"
    },
    {
      "index": 7,
      "name": "Hanging Display",
      "purpose": "悬挂展示，衣架上展示，展现产品廓形和蓬松度",
      "composition_notes": "产品挂在衣架上，展现整体廓形，产品占85%，看起来挺括有质感",
      "positive_prompt": "Based on the reference product image, professional product photography of {{start.product_color}} {{start.product_category}} hanging on clothes hanger, showing full silhouette and form, pure white background RGB(255,255,255), centered composition, product looks crisp and full, studio lighting, professional e-commerce photography, 8K resolution, detailed and sharp",
      "negative_prompt": "text, watermark, wrinkled, crumpled, person, shadow, blur, low quality, dark, distorted shape"
    }
  ]
}
```

### 4.5 配置输出变量

```
输出变量名：prompts_json
变量类型：String
说明：包含7张图完整提示词的JSON
```

点击「**完成**」。

---

## 第五步：节点四 - 代码节点（解析JSON）

### 5.1 添加代码节点

右键 → 「**添加节点**」→ 搜索「代码」→ 点击「**代码执行**」

### 5.2 配置基础信息

**节点名称**：`解析提示词JSON`

**编程语言**：`Python 3`

### 5.3 填写代码

在代码框中复制粘贴：

```python
import json
import re

def main(prompts_json: str) -> dict:
    """
    解析LLM返回的JSON字符串，提取7张图的提示词和说明
    """
    # 清理可能的markdown代码块标记
    clean_json = prompts_json.strip()
    
    # 去掉```json```标记
    if clean_json.startswith("```"):
        clean_json = re.sub(r'^```[a-z]*\n?', '', clean_json)
        clean_json = re.sub(r'\n?```$', '', clean_json)
    
    # 解析JSON
    try:
        data = json.loads(clean_json.strip())
        images = data.get("images", [])
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse error: {str(e)}"}
    
    # 提取每张图的信息
    result = {}
    for img in images:
        i = img.get("index", 0)
        result[f"prompt_{i}"] = img.get("positive_prompt", "")
        result[f"negative_{i}"] = img.get("negative_prompt", "")
        result[f"name_{i}"] = img.get("name", "")
        result[f"purpose_{i}"] = img.get("purpose", "")
    
    # 总数
    result["total_images"] = len(images)
    
    return result
```

### 5.4 配置输入和输出

**输入变量**（自动检测）：
```
prompts_json → 来自「生成图像提示词」节点的输出
```

**输出变量**（代码自动生成，会包含）：
```
prompt_1, negative_1, name_1, purpose_1
prompt_2, negative_2, name_2, purpose_2
...
prompt_7, negative_7, name_7, purpose_7
total_images
```

点击「**完成**」。

---

## 第六步：并行节点组 - 7个图生图节点

### 6.1 添加并行节点容器

右键 → 「**添加节点**」→ 搜索「并行」→ 点击「**并行**」

**节点名称**：`图生图并行处理`

### 6.2 在并行节点内添加7个图像节点

点击并行节点 → 右键内部 → 「**添加节点**」→ 搜索「图像」→ 点击「**图像生成**」

重复7次，每次都在并行节点内添加。

---

### 6.3 配置图像节点1（其他6个雷同）

**点击第一个图像节点，右侧配置面板填写：**

**节点名称**：`生成图片1_正面主图`

**基础参数**：
```
模式：Image-to-Image（图生图）
模型：选择下列之一
  推荐1：Flux Kontext（最新，保真度最高）
  推荐2：Stable Diffusion XL（稳定，广泛支持）
  可选：GPT-Image-1
```

**图片参数**：
```
参考图片/Source Image：{{start.product_image}}
图片尺寸（Size）：1024 x 1024
图片质量（Quality）：HD
生成数量（Count）：1
```

**提示词参数**：
```
正向提示词（Positive Prompt）：{{step_4.prompt_1}}
负向提示词（Negative Prompt）：{{step_4.negative_1}}
```

**关键参数 - 图片相似度（Image Strength / Denoising）**：
```
Strength：0.35
（这个参数最关键！决定生成图和原图的相似程度）
```

**其他参数**：
```
Guidance Scale（引导强度）：7.5
Seed（随机种子）：留空（每次随机）
```

点击「**完成**」。

---

### 6.4 配置图像节点2-7（快速方式）

复制图像节点1，然后修改以下内容：

**图像节点2**：
```
节点名称：生成图片2_反光条特写
正向提示词：{{step_4.prompt_2}}
负向提示词：{{step_4.negative_2}}
Strength：0.45
```

**图像节点3**：
```
节点名称：生成图片3_背面展示
正向提示词：{{step_4.prompt_3}}
负向提示词：{{step_4.negative_3}}
Strength：0.55
```

**图像节点4**：
```
节点名称：生成图片4_平铺功能图
正向提示词：{{step_4.prompt_4}}
负向提示词：{{step_4.negative_4}}
Strength：0.50
```

**图像节点5**：
```
节点名称：生成图片5_45度角立体
正向提示词：{{step_4.prompt_5}}
负向提示词：{{step_4.negative_5}}
Strength：0.55
```

**图像节点6**：
```
节点名称：生成图片6_功能细节特写
正向提示词：{{step_4.prompt_6}}
负向提示词：{{step_4.negative_6}}
Strength：0.40
```

**图像节点7**：
```
节点名称：生成图片7_悬挂展示
正向提示词：{{step_4.prompt_7}}
负向提示词：{{step_4.negative_7}}
Strength：0.50
```

---

## 第七步：节点五 - LLM节点3（使用说明和建议）

### 7.1 添加第三个LLM节点

右键 → 「**添加节点**」→ 「**LLM**」

**节点名称**：`生成使用说明`

**模型**：GPT-4o-mini（或 Claude 3 Haiku，省token）

**参数**：
```
Temperature：0.5
Max Tokens：2000
```

### 7.2 System Prompt

```
你是亚马逊产品listing优化专家，帮助卖家正确使用AI生成的产品图。
输出内容必须用中文，简洁清晰，条理分明。
```

### 7.3 User Prompt

```
已为产品「{{start.product_name}}」生成了7张亚马逊主图。

产品类别：{{start.product_category}}
产品颜色：{{start.product_color}}

请提供使用建议，包括：

1. **每张图的用途说明**：简述每张图应该放在亚马逊的哪个位置（第1主图、第2主图等或副图），以及为什么
2. **每张图的核心卖点**：用一句话总结每张图想表达的卖点
3. **上传注意事项**：
   - 文件格式和大小建议
   - 哪些图必须是真实产品照片（第1张必须）
   - 哪些图可以是AI生成的（建议用于第2-7张主图）
4. **后期处理建议**：如果某些图的白背景不够纯净，如何用工具处理
5. **优化建议**：如果某张图效果不理想，应该如何调整参数重新生成

输出格式：
- 每张图用"【图N】"作为标题
- 条目用"1. 2. 3."编号
- 可用**加粗**强调重点
```

### 7.4 输出变量

```
输出变量名：usage_guide
变量类型：String
说明：中文使用指南和建议
```

点击「**完成**」。

---

## 第八步：结束节点（End）

### 8.1 添加结束节点

右键 → 「**添加节点**」→ 搜索「结束」→ 点击「**结束**」

**节点名称**：`工作流输出`

### 8.2 添加输出变量

依次添加以下输出（这些是用户最终能拿到的结果）：

| 输出变量 | 来源 | 说明 |
|---------|------|------|
| `image_1` | 并行节点 → 图像节点1 → output | 正面主图URL |
| `image_2` | 并行节点 → 图像节点2 → output | 反光条细节URL |
| `image_3` | 并行节点 → 图像节点3 → output | 背面展示URL |
| `image_4` | 并行节点 → 图像节点4 → output | 平铺功能图URL |
| `image_5` | 并行节点 → 图像节点5 → output | 45度角URL |
| `image_6` | 并行节点 → 图像节点6 → output | 细节特写URL |
| `image_7` | 并行节点 → 图像节点7 → output | 悬挂展示URL |
| `usage_guide` | LLM节点3 → usage_guide | 使用说明文案 |
| `product_analysis` | LLM节点1 → analysis_result | 产品分析JSON |

**添加方式**：
- 点击结束节点右侧面板「**添加输出**」
- 每次填写一个输出变量的名称
- 然后在下方的「数据源」里，通过连线或输入框指向对应节点的输出
  
  例如 `image_1` 的数据源填：`{{parallel_node.image_node_1.output}}`
  
  （具体路径根据你的节点名称调整）

---

## 第九步：连接节点

现在所有节点都创建好了，需要用连线把它们连起来。

### 连接顺序（从上到下）

```
开始 → LLM1(分析) → LLM2(提示词) → 代码(解析) → 并行(7个图) → LLM3(说明) → 结束
```

**具体操作**：
1. 点击「LLM1(分析)」节点下方的圆形连接点
2. 拖动连线到「LLM2(提示词)」节点上方的连接点
3. 重复此过程连接所有节点

连接完成后，你的工作流应该看起来像一条流水线。

---

## 第十步：保存和发布工作流

### 10.1 保存工作流

点击右上角「**保存**」按钮。

### 10.2 发布工作流

点击「**发布**」按钮，选择：
- 工作流可见性：`公开` 或 `个人私密`
- 添加描述：`AI生成7张符合亚马逊规范的PPE产品主图`

点击「**确认发布**」。

---

## 第十一步：测试工作流

### 11.1 创建测试数据

发布后，点击「**运行**」或「**创建对话**」，填入测试数据：

```
产品名称：High Visibility Reflective Safety Vest
产品类别：vest
主色调：Yellow
反光条类型：2-inch silver reflective strips
安全认证：ANSI/ISEA 107 Class 2
核心功能：6 pockets, zipper front, adjustable waist straps
使用场景：construction, road work, traffic control
价格定位：mid-range
产品材质：100% polyester mesh
产品参考图：[上传你的白底背心图]
```

### 11.2 查看运行结果

工作流开始执行（从上到下依次运行每个节点），你可以看到：
1. 每个节点的运行状态（运行中/完成/出错）
2. 每个节点的输出结果（JSON、提示词等）
3. 最后7张生成的图片URL

### 11.3 调试和优化

如果某一步出错：

| 问题 | 解决方案 |
|------|--------|
| LLM输出不是JSON | 在System Prompt加一句"只输出JSON，绝不加```标记" |
| 代码节点报JSON错误 | 检查LLM的输出，确保是有效的JSON |
| 图片生成失败 | 检查参考图片URL是否有效；降低Strength值（如0.3） |
| 图片背景不够白 | 在提示词里加强化：`completely white background, no gradient` |
| 图片和原品差异太大 | 提高Strength值（如0.6）；使用质量更好的参考图 |

---

## 第十二步：集成到微信

工作流搭建完成后，可以通过以下方式在微信使用：

### 方案A：WorkBuddy微信集成（推荐）
1. 在WorkBuddy中配置微信绑定（见前面的微信接入指南）
2. 在WorkBuddy中创建一个Coze Bot集成，链接这个工作流
3. 在微信里直接调用工作流

### 方案B：Coze官方集成
1. 在Coze中打开这个工作流
2. 点击「**集成**」→ 「**微信公众号**」或「**微信小程序**」
3. 按指引完成配置

---

## 快速参考表

### 各节点的关键Strength值

| 图片序号 | 内容 | 推荐Strength | 理由 |
|--------|------|-----------|------|
| 1 | 正面主图 | 0.35 | 最接近原图，保留品质感 |
| 2 | 反光条特写 | 0.45 | 中等变化，展现反光效果 |
| 3 | 背面展示 | 0.55 | 较大变化，改变角度 |
| 4 | 平铺功能 | 0.50 | 中等变化 |
| 5 | 45度角 | 0.55 | 较大变化，展现立体感 |
| 6 | 细节特写 | 0.40 | 稍保留产品细节 |
| 7 | 悬挂展示 | 0.50 | 中等变化 |

---

## 常见问题FAQ

**Q: 能否用真实产品照片作为参考图？**
A: 完全可以，而且强烈推荐。你的白底产品照片越清晰专业，生成的图片越接近真实产品。

**Q: 为什么第1张图Strength设得最低（0.35）？**
A: 因为第1张是正面主图，最重要的是保留真实产品的外观。Strength低意味着更忠实于参考图。

**Q: 如果生成的某张图不满意怎么办？**
A: 可以单独运行那一个图像节点，修改提示词或Strength值后重新生成，不需要跑整个工作流。

**Q: 7张图生成需要多长时间？**
A: 并行处理下，通常5-10分钟。具体取决于模型速度和系统负载。

**Q: 能否一次生成多个产品的图？**
A: 目前这个工作流设计是单产品流程。如需批量处理，可以创建多个对话分别运行。

---

## 下一步

1. ✅ 按照上述步骤搭建工作流
2. ✅ 用一个反光背心产品进行完整测试
3. ✅ 根据测试结果调整提示词和Strength值
4. ✅ 绑定微信，开始在微信里一键生成产品主图
5. ✅ 在亚马逊Seller Central中上传生成的图片

祝你的PPE产品销量爆增！🚀
