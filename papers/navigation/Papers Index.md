# Papers Index

<!-- Papers Index — maintained by hand. One entry per dedupe key. -->

## Imitation Learning / Teleoperation / Manipulation

- [[papers/notes/2304.13705-ALOHA-ACT|ALOHA + ACT：Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware]] — RSS 2023，低成本遥操硬件 + Action Chunking with Transformers。 <!-- dedupe: arxiv:2304.13705 -->
- [[papers/notes/2506.16685-CR-DAgger|CR-DAgger：Compliant Residual DAgger]] — NeurIPS 2025，顺应干预接口 + 残差策略修正。 <!-- dedupe: arxiv:2506.16685 -->

## Force-Aware / Contact-Rich Manipulation

- [[papers/notes/2411.15753-FoAR|FoAR：Force-Aware Reactive Policy]] — arXiv 2024（SJTU），学未来接触概率 φ 门控力融合 + reactive control。 <!-- dedupe: arxiv:2411.15753 -->
- [[papers/notes/2606.08555-FAWAM|FAWAM：Force-Aware World Action Models]] — arXiv 2026（PKU+SJTU），世界模型联合预测动作+未来 wrench，力差值驱动残差纠正闭环。 <!-- dedupe: arxiv:2606.08555 -->
- [[papers/notes/2509.07962-TA-VLA|TA-VLA：Torque-aware VLA 设计空间]] — CoRL 2025，无传感器关节力矩(电机电流反算)塞进预训练 VLA：进 decoder / 历史压单 token / 预测未来力矩。 <!-- dedupe: arxiv:2509.07962 -->
- [[papers/notes/2505.22159-ForceVLA|ForceVLA：Force-aware MoE]] — arXiv 2025（复旦+SJTU），FVLMoE 把外置 6 轴力与视觉语言在 MoE 里深度融合；会融>有力，力须 VLM 后进。 <!-- dedupe: arxiv:2505.22159 -->
- [[papers/notes/2602.23648-FAVLA|FAVLA：Force-Adaptive Fast-Slow VLA]] — arXiv 2026，快-慢双频：慢 VLM + 高频力反应 AE，每层 cross-attn 注入 + 预测力波动自适应调频；峰值接触力更低。 <!-- dedupe: arxiv:2602.23648 -->
- [[papers/notes/2502.17432-FACTR|FACTR：Force-Attending Curriculum Training]] — arXiv 2025（CMU），架构无关的训练式路线：课程糊视觉逼策略去用力(外部关节力矩)，未见物体泛化 +40%。 <!-- dedupe: arxiv:2502.17432 -->

> 方法论综述见 [[力信息如何融入模型]](力进模型的设计空间)与 [[force-aware-manipulation]](力在模仿学习中的使用谱系)。
