# VLA 训练与基础概念

> 面向新手的 VLA(Vision-Language-Action Model)入门笔记,配合提问逐步扩充。

## 一、VLA 是什么

**VLA = Vision-Language-Action Model**(视觉-语言-动作模型)。

一句话概括:**输入图像和自然语言指令,输出机器人动作**。

思想脉络:

```
LLM (语言 → 语言)
  ↓ 加视觉编码器
VLM (图像+语言 → 语言)     例如 LLaVA、PaLI、Qwen-VL
  ↓ 加动作输出头
VLA (图像+语言 → 动作)     例如 RT-2、OpenVLA、π0
```

VLA 的骨架**基本就是一个 VLM**,只是把「输出文本 token」改成或扩展成「输出动作」。

## 二、基本概念

### 0. 深度学习/Transformer 通用术语速查

这些术语在 VLA 里反复出现,先集中过一遍。

**Backbone(骨干网络)**:模型的主体特征提取部分,把原始输入变成高维特征向量。相对的是 **head(输出头)**,做最后的任务特定输出。类比:车的底盘+发动机是 backbone(所有车型共用),车身样式是 head。VLA 里 backbone 通常是预训练 VLM(PaliGemma / Qwen-VL / Llama),head 是 MLP / Transformer decoder / Diffusion / Flow Matching 中的一种。

**Encoder / Decoder(编码器 / 解码器)**:Transformer 架构的两半。原始 Transformer 是 Encoder-Decoder(翻译:encoder 读英文,decoder 生成中文);现代 LLM(GPT)是 **decoder-only**。Decoder 的关键特征:
- **Causal mask(因果掩码)**:预测第 t 个 token 时只能看前 t-1 个,不能偷看未来
- **可带 cross-attention**:当前 token 去"查询"另一堆特征(如 VLA 里查 backbone 特征)
- **作用**:一步步生成序列。文字 decoder 生成词,动作 decoder 生成动作步

**Query(查询)/ Action Query(动作查询)**:可学习的向量(learnable embedding)。想输出 N 步动作就准备 N 个"空 token",让它们通过 attention 从 backbone 特征里"提问",拿到自己那一步需要的信息。**每个 query 对应动作序列的一步**。这个思路来自 DETR 的 object query。

**Linear(线性层 / Dense / FC)**:最简单的神经网络层,`y = W·x + b`。作用是把一个维度的向量映射到另一个维度。堆几层 Linear + ReLU 就是 MLP。

**Chunk(动作块)**:一段打包的连续动作序列。20Hz 控制、一次预测未来 16 步 = 0.8 秒的动作,这 16 步就是一个 action chunk,shape = (chunk_len, action_dim)。参见后面 §二.3 Action Chunking。

**MSE(Mean Squared Error,均方误差)**:回归任务最常用的损失函数,`MSE = (1/N)·Σ(y_pred - y_true)²`。特点:可导、对大误差敏感(平方放大)、数学简单好调。**Flow matching 用 MSE 好调**的原因:它把"生成"问题转成"回归速度"问题,损失曲面平滑,不用像 diffusion 那样调 noise schedule。

**ReLU / GELU / SwiGLU** 等:**激活函数**,给神经网络加非线性,让它能学习复杂映射。ReLU = `max(0, x)`,最经典;LLM 里现在多用 GELU / SwiGLU。

**Cross-attention vs Self-attention**:
- **Self-attention**:序列内部元素互相看(动作 chunk 内部,第 5 步看第 1~4 步)
- **Cross-attention**:一个序列去"查询"另一个序列(动作 query 去查图像 token)

#### Attention 详解:Q, K, V 三兄弟

Attention 说白了就是**查字典**:你有个问题(Query),字典里每一条有个索引(Key)和内容(Value),根据 Q 和 K 的匹配程度决定从 V 里拿多少内容。

**公式**:

```
Attention(Q, K, V) = softmax(Q·Kᵀ / √d) · V
```

Q, K, V 的算法:

```
Q = X_query · W_Q       ← 问什么
K = X_kv    · W_K       ← 每条内容的"索引"
V = X_kv    · W_V       ← 每条内容的"实际内容"
```

关键:**`X_query` 和 `X_kv` 是不是同一个东西**,决定 self 还是 cross。

**Self-attention:Q, K, V 全部来自同一序列**

```
X ─┬→ ·W_Q → Q
   ├→ ·W_K → K
   └→ ·W_V → V     → Attention(Q, K, V)
```

- **直觉**:序列内每个 token 互相看,决定"我该关注序列里的哪些其他位置"
- **例子**:句子 `"The cat sat on the mat"` 里,`"sat"` 会强烈关注 `"cat"`(主语),中等关注 `"mat"`(位置)
- **VLA 里**:图像 patch 之间(理解空间关系)、语言 token 之间(理解句意)、动作 chunk 内部(保证连贯)

**Cross-attention:Q 来自 A,K/V 来自 B**

```
X_query ── ·W_Q → Q         (来自 A,比如动作 query)
X_kv ──┬── ·W_K → K         (来自 B,比如 backbone 特征)
       └── ·W_V → V
                     → Attention(Q, K, V)
```

- **直觉**:一个序列去"查询"另一个序列,从对方拿信息
- **例子**:翻译 `"I love cats" → "我爱猫"`,decoder 生成"猫"时,cross-attention 让"猫"query 强烈关注 encoder 里的"cats"
- **VLA 里**:16 个动作 query cross-attend 图像+语言 token —— query 0 可能看图像左侧的物体和指令"pick up",query 15 可能看目标位置和"place on plate"

**对比**

| 维度 | Self-attention | Cross-attention |
|---|---|---|
| Q 来源 | 序列 X | 序列 A |
| K, V 来源 | 序列 X(**同一个**) | 序列 B(**不同**) |
| 输出长度 | = 输入长度 | = Q 的长度,可和 K/V 不同 |
| 作用 | 序列内部关系 | 一个序列从另一个序列取信息 |
| 典型用途 | 理解一句话、一张图 | 翻译、生成、多模态融合 |

**一个完整 decoder block 长这样**

```
输入(动作 query 序列)
    ↓ Self-attention   ← query 之间互相协调(动作步依赖)
    ↓ Cross-attention  ← query 去查 backbone 特征(取图像/语言信息)
    ↓ FFN (MLP)        ← 逐位置非线性变换
    ↓ 输出
```

Self-attention 保证 chunk 内部连贯,cross-attention 保证动作和观测对齐。

**和力信息融合的关系**(参见 [[力信息如何融入模型]]):力信息融合的常见做法就是让动作 query **cross-attend 力信号 token**,相当于生成动作时"顺便问一下力反馈的意见"。

### 1. 模态(Modality)

指信息的类型。VLA 主要三种:

- **Vision**:摄像头图像(单视角、多视角、腕部相机、第三人称相机)
- **Language**:任务指令,例如 "把红色积木放到盘子里"
- **Action**:机器人的低层控制信号(关节角、末端位姿、夹爪开合等)

近期研究里越来越多的**附加模态**:

- **Proprioception 本体感知**:机器人当前关节位置、速度
- **Force/Torque 力/力矩**:六维力传感器读数 —— 参见 [[力信息如何融入模型]]
- **Tactile 触觉**:指尖压力/图像
- **Depth 深度**:RGB-D 相机

### 2. Action 的表示方式

VLA 训练里最关键的设计决策之一,主要有三派:

| 方式            | 代表工作                  | 做法                                                                              |
| ------------- | --------------------- | ------------------------------------------------------------------------------- |
| **离散化 token** | RT-2, OpenVLA         | 把每个动作维度离散化成 256 个 bin,当作词表里的 token,像生成文字一样生成                                    |
| **连续回归头**     | ACT, Diffusion Policy | 在 backbone 后面接一个 MLP / Transformer decoder / Diffusion / Flow Matching,直接输出连续动作 |
| **混合**        | π0, π0.5              | VLM backbone + flow matching action expert                                      |

#### 连续回归头的四种做法详解

这四个是"backbone 特征 → 连续动作"的四种映射,**复杂度递增**。前两个是**确定性回归**(一个输入 → 一个输出),后两个是**生成模型**(能建模分布,采样出动作)。

**① MLP(Multi-Layer Perceptron,多层感知机)**

最简单的神经网络,几层全连接堆起来:

```
backbone 特征 → Linear+ReLU → Linear+ReLU → Linear → 动作向量
```

- 优:简单快
- 缺:遇到"同一观测有多种合理动作"(多模态分布)时,会把它们**平均**成一个不合理的动作。经典失败例子:数据里人有时绕左有时绕右,MLP 平均后**直接撞上去**
- 代表:早期 BC 方法

**② Transformer decoder**

Transformer 里的解码器结构,两个关键机制:

- **Self-attention**:输出序列内部互相看(第 5 步动作能看到前 4 步)
- **Cross-attention**:输出去查询 backbone 特征(每步从图像/语言 token 读信息)

典型接法(ACT):准备 N 个可学习的"动作 query token" → cross-attention 从 backbone 取信息 → self-attention 互相协调 → 每个 query 输出一个 7 维动作 → 拼成 chunk

- 优:天然适合输出序列(action chunk)
- 缺:仍是确定性回归,多模态问题没根本解决(ACT 靠 CVAE 加 latent 部分缓解)
- 代表:ACT

**③ Diffusion(扩散模型)**

生成模型,思想是"学一个去噪过程"。

- **训练**:给真实动作 a₀ 逐步加高斯噪声得到 a_T ≈ 纯噪声。模型学 `ε_θ(a_t, t, condition)`,预测当前加了什么噪声
- **推理**:从纯噪声出发,反向去噪 50~100 步 → 真实动作
- **直觉类比**:雕刻大理石,从粗糙石头一刀刀削出雕像

优:天然建模多模态分布,鲁棒
缺:推理慢(50~100 次网络前向),实时控制吃力
代表:**Diffusion Policy**

**④ Flow Matching(流匹配)**

Diffusion 的"堂兄弟",数学更简洁、推理更快。**π0 用的就是这个**。

**核心思想**:学"从噪声分布流向数据分布的速度场"。想象一条河,上游是高斯噪声,下游是真实动作,flow matching 学**河水在每处的流速** v(x, t)。

- **训练**:
  1. 采样真实动作 a₁、噪声 a₀ ~ N(0, I)、时间 t ∈ [0, 1]
  2. 构造插值 a_t = (1-t)·a₀ + t·a₁
  3. 模型预测速度 v_θ(a_t, t, condition),目标是 a₁ - a₀
  4. MSE 损失
- **推理**:从 a₀ ~ N(0, I) 出发,`a_{t+dt} = a_t + v·dt`,通常 5~10 步搞定

**相比 diffusion 的优点**:
- 推理步数少一个数量级(5~10 步 vs. 50~100 步),实时控制友好
- 数学简洁,损失就是 MSE,训练稳定

代表:**π0 / π0.5**;生图领域 Stable Diffusion 3、Flux 也用它

**四种做法对比**

| 方法                    | 类型    | 一次前向?          | 多模态?  | 推理速度 | 代表              |
| --------------------- | ----- | -------------- | ----- | ---- | --------------- |
| **MLP**               | 确定性回归 | ✅              | ❌     | 最快   | 早期 BC           |
| **Transformer decoder** | 确定性回归 | ✅              | ⚠️ 弱  | 快    | ACT             |
| **Diffusion**         | 生成模型  | ❌ (50~100 步)   | ✅     | 慢    | Diffusion Policy |
| **Flow Matching**     | 生成模型  | ❌ (5~10 步)     | ✅     | 中等   | π0              |

**演化脉络**

```
MLP                     太简单,平均掉多模态
  ↓ 引入序列 / attention
Transformer decoder     能建模动作序列,但还是确定性
  ↓ 引入随机性,建模分布
Diffusion               能采多模态,但慢
  ↓ 简化数学,减少推理步数
Flow Matching           又快又能建模分布,当前主流
```

### 3. Action Chunking(动作分块)

**不预测下一步动作,而是一次预测未来 N 步(如 16 步)的动作序列**,然后执行前 K 步再重新预测。ACT 论文提出的思路,现在几乎所有 SOTA VLA 都在用。

好处:缓解 compounding error、动作更平滑。

### 4. Episode / Trajectory / Demonstration

- **Episode**:一次完整的任务执行,例如「从开始抓取到把杯子放到目标位置」
- **Trajectory**:一条 episode 内的时间序列 `(o_t, a_t, o_{t+1}, a_{t+1}, ...)`
- **Demonstration**:人类通过遥操作(teleoperation)采集的示教数据

### 5. Teleoperation 遥操作

人操作主端设备(ALOHA 主从、SpaceMouse、VR 手柄),机器人从端跟随运动,同时录制相机图像 + 关节角 + 指令。**目前主流 VLA 训练数据的主要来源**。

### 6. Cross-embodiment 跨本体

不同机器人(Franka、UR5、xArm、双臂 ALOHA…)自由度、动作空间都不同。近年的大规模 VLA(OpenVLA、RT-X、π0)会**混合多种本体的数据**一起训,让模型泛化到多种硬件。

**Open X-Embodiment (OXE)** 是最著名的开源数据集集合。

## 三、VLA 的训练流程

现代 VLA 通常是**多阶段训练**。

### 阶段 0:VLM 预训练(通常直接用现成的)

用互联网规模的图文数据训练 VLM,让模型学会「看图 + 读文字」。一般不自己做,直接用 PaliGemma、Llama-2、Qwen2-VL 等开源 VLM 当骨架。

#### Vision encoder 和 language backbone 怎么拼接

**核心思路**:把图像也变成一串"token",和文本 token 同维度,然后拼在一起交给 LLM。

**三步走**:
```
图像 → [Vision Encoder] → 视觉特征 → [Projector] → 视觉 token(维度对齐 LLM)
                                                       ↓
                                       拼接 [视觉 token] + [文本 token] → LLM
```

**Step 1: Vision Encoder(图像 → 视觉特征)**

主流是 ViT 家族(SigLIP、CLIP、DINOv2):

```
图像 224×224 → 切 16×16 patch → 14×14 = 196 个 patch
   → 每个 patch 展平+Linear → patch embedding
   → 加位置编码 → 过 ViT Transformer
   → 输出 196 个特征向量(每个 patch 一个)
```

直觉:把图像当作"196 个 patch 组成的序列",用 Transformer 处理,和处理文字一样。

**Step 2: Projector(维度对齐)**

Vision encoder 输出维度(如 1024)和 LLM 嵌入维度(如 4096)不一样,用 2 层 MLP 做投影:

```
视觉特征 (196 × 1024) → Linear+GELU+Linear → 视觉 token (196 × 4096)
```

Projector 是训练里最关键的"翻译器",把视觉世界向量翻译成 LLM 能懂的"语言"。

**Step 3: 拼接进 LLM**

```
输入 = [视觉 token × 196] [文本 token × M] [动作 query / 动作 token]
        → LLM 全部当一串向量做 self-attention
        → LLM 靠 attention 自己学视觉和文本的对应关系
```

**三种主流架构**

| 架构 | 做法 | 代表 | 优 | 缺 |
|---|---|---|---|---|
| **Linear Projection** | MLP 投影直接拼 | LLaVA, PaliGemma, **OpenVLA**, Qwen2-VL, π0 | 简单,权重完整复用 | 视觉 token 多(196~729)吃上下文 |
| **Q-Former** | 32 个 learnable query 用 cross-attention 压缩视觉特征 | BLIP-2, MiniGPT-4 | token 数少 | 有信息损失,已不流行 |
| **交错 Cross-attention** | 不拼接,在 LLM 层里插 cross-attention 让文本查视觉 | Flamingo, Idefics | 不占 sequence length | 改架构,权重不能直接复用 |

**现代 VLA 的实际拼接**

OpenVLA:
```
[SigLIP token × 729] + [DINOv2 token × 729]    ← 双 vision encoder
  + [语言 token × ~20]
  + [动作 token × 7]
  → Llama-2 7B (decoder-only, causal self-attention)
```

π0(混合架构):
```
[SigLIP token] + [文本 token] + [proprio token]
  → PaliGemma (~3B) 提取 KV cache
  → Action Expert (~300M) 通过 cross-attention 查 PaliGemma KV
  → flow matching 生成 action chunk
```

**实用细节**

- **多视角相机**:每个视角单独过 vision encoder,视觉 token 并列拼接,靠位置编码或"视角标签 token"区分
- **Proprioception**:小 MLP(7 → 4096)把关节向量变成 1 个 token 拼进序列
- **力信息**:同样思路,6 维 F/T → MLP → 1 个 force token 拼进序列(参见 [[力信息如何融入模型]] 的 late fusion)
- **视觉 token 数量权衡**:224×224 → 196,384×384 → 729,分辨率越高精度越好但 attention 是 O(N²),推理越慢。有些工作用 token merging 减少

**一张图总结**

```
[图像]─ViT─►[196 vec, d=1024]─MLP─►[196 vec, d=4096]─┐
                                                      │
[文本]─tokenizer─►[M tokens, d=4096]──────────────────┼─►拼接─►LLM─►输出
                                                      │
[proprio]─MLP─►[1 vec, d=4096]────────────────────────┘
```

所有模态经过各自的 encoder + projector,统一到**同一嵌入维度**,拼成序列交给 LLM。这就是"多模态融合"最本质的做法。

### 阶段 1:大规模机器人数据预训练(Robotics Pretraining)

- **数据**:Open X-Embodiment 这类大杂烩,几百万条轨迹,覆盖上百种任务、多种机器人
- **目标**:让 VLM 学会把「图像 + 指令」映射到「动作」的通用能力
- **动作头**:
  - 离散 token 派:动作 token 拼在文本 token 后面用 next-token prediction
  - Diffusion / Flow matching 派:同时训练 backbone + action expert

### 阶段 2:任务/场景微调(Fine-tuning)

- **数据**:自己采集的目标任务数据,通常几十到几千条示教
- **目的**:让通用 VLA 适配你的机器人、场景、任务
- **技巧**:LoRA、只训 action head、全量微调 —— 看数据量和算力

#### 微调策略详解

**策略 A:只训 head(冻结 backbone)**

```
backbone (❄️ 冻结)  →  head (🔥 训练)
```
- 优:省显存,训得快
- 缺:backbone 视觉/语言理解没法适配新场景,分布差异大时效果差
- 适用:数据极少(<50 条)、算力紧、场景接近预训练分布

**策略 B:LoRA(现在最主流,OpenVLA 官方推荐)**

Low-Rank Adaptation:在 backbone 每个线性层旁边插入两个小矩阵(rank=8 或 16),只训小矩阵,原始权重冻结。

```
原始:    y = W·x                    (W 冻结)
LoRA:    y = W·x + (B·A)·x          (A, B 训练,秩很小)
```
- 优:参数量 <1%,显存友好,效果接近全量
- 缺:极难任务上仍有差距
- 适用:大部分场景(几百到几千条数据)

**策略 C:全量微调(full fine-tuning)**

所有参数都训。
- 优:上限最高
- 缺:显存爆炸(7B 模型要几十 GB)、易过拟合、需要仔细调学习率
- 适用:数据量大(>5000 条)、算力充足、场景和预训练分布差很远

**附加技巧:分层学习率**

不管 B 还是 C,常见做法:head 用大学习率(1e-3),backbone 用极小学习率(1e-5 ~ 1e-6),避免破坏预训练知识。

**决策速查**

| 数据量 | 推荐策略 |
|---|---|
| < 50 条 | 只训 head |
| 50 ~ 500 条 | **LoRA** |
| 500 ~ 5000 条 | **LoRA**(rank 调大) |
| > 5000 条 | 全量微调 |

### 阶段 3(可选):后训练 / 在线学习

RL 微调、DAgger、residual policy 等等。目前还不成熟,大多数落地系统只做到阶段 2。

## 四、训练时的具体做法

### 离散 token 派(RT-2 / OpenVLA)

一个训练样本:

```
输入:
  <image_1> <image_2> ...     ← 视觉 token(vision encoder 输出 project 到语言空间)
  "Pick up the red cube"       ← 指令 token
输出(要学的):
  <act_x> <act_y> <act_z> <act_roll> <act_pitch> <act_yaw> <act_gripper>
```

每个 `<act_*>` 是从 [-1, 1] 或关节角范围离散化成 256 个 bin 的一个 token。**损失就是标准的 cross-entropy**,和训 LLM 一模一样。

#### 什么是 bin?(离散化 / 分桶)

**Bin = "箱子/桶"**,把一个连续数值范围切成若干个小区间,每个区间就是一个 bin。这是把**连续值变离散值**最简单的方法,术语叫 **binning / discretization / 分桶**。

**具体例子**:动作范围 `[-1, 1]` 切 256 个 bin:

```
bin 宽度 = (1 - (-1)) / 256 = 2/256 ≈ 0.0078

bin 0   → [-1.0000, -0.9922)   → token id = 32000
bin 1   → [-0.9922, -0.9844)   → token id = 32001
...
bin 128 → [-0.0039,  0.0039)   → token id = 32128   ← 中间,大约"不动"
...
bin 255 → [ 0.9922,  1.0000]   → token id = 32255
```

采集到真实动作 `x_vel = 0.35`:
1. 定位 bin:`(0.35 - (-1)) / 0.0078 ≈ 172` → bin 172
2. 查表得到 **token id**(比如 32172)
3. 训练目标是让模型在这个位置输出 token id 32172

**为什么这么做**:VLM 天然只会**输出词表里的 token**,没法直接吐 "0.35" 这种浮点数。所以 RT-2 / OpenVLA 在词表里划出 256 个位置(比如 id 32000 ~ 32255),重新解释为"动作 token",分别对应 256 个 bin。模型输出这些 token 的方式和输出 "cat" "dog" 完全一样。

**推理时反过来**:模型输出 token id 32172 → 查表知道是 bin 172 → 取 bin 的中心值 → 反归一化回真实动作值 → 发给机器人。

**为什么选 256**:
- 一个字节能表示,方便处理
- 精度够用:`2/256 ≈ 0.008`,对末端速度、位置增量足够精细
- 不占太多词表:7 自由度 × chunk 16 步 = 112 个 token,可接受

**缺点**:
- **量化误差**:bin 里所有的值都被压缩成一个代表值
- **不同维度共享 bin 划分不合理**:手指开合和末端位移的分辨率需求完全不同
- 这也是为什么 π0 转向 flow matching / diffusion,直接输出连续值

#### 每个维度是不是都有独立的 bin?

**准确说法**:每个动作维度**独立归一化**,但**共享同一套 256 个 bin 的 token id**。

**分维度独立的部分:范围归一化**

7 自由度动作 `[dx, dy, dz, droll, dpitch, dyaw, gripper]` 的物理量级差得很远:

```
dx     ≈ [-0.05, 0.05] m       (末端位移增量)
droll  ≈ [-0.3, 0.3] rad       (末端姿态增量)
gripper ≈ [0, 1]                (开合)
```

**每个维度的范围从训练集统计出来**(常见:取 1st ~ 99th 百分位,避免离群点),然后**各自**归一化到 `[-1, 1]`。

**共享的部分:bin → token id 的映射表**

归一化到 `[-1, 1]` 后,所有维度**共用**同一套 256 个 bin 的划分,共用同一套 256 个 token id。不管当前预测 dx 还是 gripper,都从这 256 个里选。

> **关键**:词表里就多出 **256 个动作 token**,复用于所有维度。同一个 token id 在不同位置代表不同物理量 —— 靠**输出序列里的位置**区分维度(位置 0 是 dx,位置 6 是 gripper,固定不变)。类比英语的 "May":句首大写是月份,句中小写是情态动词,同一个 token 靠位置和上下文切换语义。

**完整流程举例**

真实动作 `[dx=0.02, dy=-0.01, dz=0.003, droll=0.15, dpitch=0, dyaw=-0.1, gripper=0.8]`

训练时:
1. 各维度独立归一化 → `[0.4, -0.2, 0.06, 0.5, 0, -0.33, 0.6]`
2. 共用 bin 表分别查 token id → `[tok_179, tok_102, tok_136, tok_192, tok_128, tok_86, tok_204]`
3. 按固定顺序拼在文本 token 后,做 next-token prediction

推理时反过来:输出 7 个 token → 查表得 bin 中心值 → **各维度用自己的范围**反归一化 → 组装成动作。

**关键点**

- **顺序固定**:训练和推理必须按同一顺序(如 dx→dy→dz→droll→dpitch→dyaw→gripper),模型靠"位置"知道当前预测的是哪个维度
- **归一化统计量要保存**:每个维度的 min/max(或 percentile 值)是模型的一部分,推理时要用同一份统计量反归一化
- **跨本体训练**:OXE 里每个机器人有自己一套统计量,是跨本体训练的工程细节

**变体**

- **每维度独立 token id**:词表扩到 `7 × 256 = 1792` 个动作 token,主流不用(共享更省词表且效果差不多)
- **非均匀 bin**:按数据分位数划 bin(密集区更细),而不是等宽

### Flow matching / diffusion 派(π0)

- Backbone 处理 image + language + proprioception,得到 condition
- 一个专门的 action expert(小 transformer)在这个 condition 下,用 flow matching 目标去噪出未来 N 步的连续动作 chunk
- 损失是 flow matching / diffusion 的回归损失

## 五、和力信息融合的连接

参见 [[力信息如何融入模型]]。几种常见做法:

1. **Late fusion(晚融合)**:力/力矩数据编码成 token,拼到 action expert 或 policy head 的输入里(FoAR、FAWAM)
2. **Early fusion(早融合)**:力当作和视觉并列的一路模态,进 VLM backbone 一起做 self-attention(FACTR)
3. **Residual policy / dual-stream**:主 VLA 出粗动作,力反馈驱动一个残差 policy 做精调(Force-VLA)
4. **作为条件而非输入**:力信息不进模型,而是在采集数据时通过 compliance control 保证数据质量

## 六、新手入门路径建议

按顺序看这几篇就能把整个 VLA 图景搞清楚:

1. **RT-2**(Google, 2023):首次把 VLM 直接当 policy 用,离散 action token 的开山
2. **OpenVLA**(2024):开源版 RT-2,7B 参数,代码和权重完全公开,新手最容易上手复现
3. **ACT / Diffusion Policy**:虽然不算严格 VLA,但 action chunking / diffusion action 的鼻祖
4. **π0**(Physical Intelligence, 2024):当前 SOTA,flow matching + VLM backbone,是很多力融合工作的 base model —— 详见 [[π0 系列模型]]
5. **Open X-Embodiment / RT-X**(2024):了解跨本体大数据集长什么样

想动手:从 [OpenVLA GitHub](https://github.com/openvla/openvla) 开始,LIBERO 仿真环境可以在没有真机的情况下跑通完整训练+评估 pipeline。

## 七、Benchmark(评测基准)

**Benchmark = 标准化的任务集 + 评估协议 + 指标**,让不同方法能在同一把尺子下比较。类比:AI 模型的"高考"。

**通常包含三样东西**:
1. **任务集**:一系列可复现的固定任务
2. **评估协议**:跑几次、初始状态怎么随机化、成功怎么定义
3. **指标**:通常是 **success rate(成功率)**

### 仿真 Benchmark(免真机,好复现)

| Benchmark | 平台 | 任务数 | 特点 |
|---|---|---|---|
| **LIBERO** | Robosuite | 130 | VLA 最主流,分 Spatial/Object/Goal/Long,OpenVLA/π0 都在上面报数 |
| **CALVIN** | PyBullet | 34 | 长时序、语言条件、多任务链 |
| **RLBench** | CoppeliaSim | 100+ | 老牌,任务多样 |
| **SimplerEnv** | ManiSkill | ~10 | 对齐真机 Google Robot / WidowX,预测真机表现 |
| **RoboCasa** | Robosuite | 100+ | 家庭场景多样性,近期热门 |
| **Meta-World** | MuJoCo | 50 | 主要给 RL,VLA 里用得少 |

### 真机 Benchmark(更真实但难完全复现)

- **RT-1 / RT-2 tasks**:Google 厨房任务集
- **Bridge V2**:UC Berkeley WidowX 数据集配套评测
- **DROID**:斯坦福大规模数据集配套评测
- **π0 real-world tasks**:折衣物、装袋、擦桌子 —— 工业界标杆

### 常用指标

- **Success Rate (SR)**:成功次数 / 尝试次数,最主要
- **SR under distribution shift**:换背景/物体/位置的成功率(测泛化)
- **Task completion length**:长任务里完成了几个子步骤
- **Efficiency**:时间、动作数

### LIBERO 详解(复现 OpenVLA 会遇到)

分四个子集,测不同类型泛化:

| 子集 | 变什么 | 测什么 |
|---|---|---|
| **LIBERO-Spatial** | 物体位置 | 空间泛化 |
| **LIBERO-Object** | 物体种类 | 物体泛化 |
| **LIBERO-Goal** | 任务目标 | 语言/任务泛化 |
| **LIBERO-Long** | 长时序多子任务 | 长程规划 |

每子集 10 任务 × 50 次 rollout,报平均 SR。OpenVLA 在上面约 76%,是常见基线。

### Benchmark 的意义

- **横向比较**:新方法要在同 benchmark 上和 SOTA 比才有说服力
- **消融验证**:测某个改动(如加力信息)的效果
- **发论文的入场券**:审稿人会问"有没有在 XX benchmark 上验证"

做力信息融合研究时,大概率会在 **LIBERO** 或 **SimplerEnv** 上对比 baseline VLA。

## 八、待深入的问题(随提问扩充)

- [ ] Action chunking 的具体实现细节
- [x] Flow matching 训练目标怎么写 ← 已在 §二.2 展开
- [x] Vision encoder 和 language backbone 怎么拼接 ← 已在 §三.阶段 0 展开
- [x] Action token 的离散化(bin 划分、范围归一化) ← 已在 §四 展开
- [x] LoRA 微调 VLA 的实操 ← 已在 §三.阶段 2 展开
- [ ] 力信息进 attention 的几种具体接法
