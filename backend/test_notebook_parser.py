"""
Standalone test to debug the section parser issue.
Run this to see if the parser works outside the notebook.
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agents.section import SectionAnalyzer

# Same SAMPLE_PAPER from notebook
SAMPLE_PAPER = """
# Neural Architecture Search with Reinforcement Learning

# 1. Abstract

We present a novel approach to NAS using RL. Our method achieves SOTA results on ImageNet.
The architecture it discovered outperformed manually designed architectures by a significant margin.

# 2. Introduction

Deep learning has revolutionized computer vision. However, designing neural architectures remains
a time-consuming process that requires expert knowledge. This is problematic because different
tasks may require different architectures, and it's not always clear what architecture will work
best for a given task.

In this work, we propose using RL to automatically search for optimal neural architectures.
Our approach uses a controller RNN to generate architecture descriptions, which are then trained
and evaluated. The validation accuracy is used as the reward signal to train the controller.

# 3. Methods

This section describes our neural architecture search methodology, including the search space
design and training procedures.

## 3.1 Architecture Search Space

Our search space includes various layer types including convolutional layers, pooling layers,
and skip connections. The controller generates a sequence of tokens that specifies the architecture.
Each token represents a decision about the architecture like layer type, kernel size, etc.

## 3.2 Training Procedure

We trained the controller using REINFORCE. The controller generates 100 architectures per iteration.
Each architecture is trained for 50 epochs on CIFAR-10. We used the validation accuracy as the
reward signal. The controller is then updated using policy gradients.

### 3.2.1 Hyperparameters

The learning rate was set to 0.001 with Adam optimizer. We used a batch size of 32 for training
the controller network.

# 4. Results

Our method discovered architectures that achieved 96.4% accuracy on CIFAR-10 test set. This
outperformed the previous best result. The discovered architecture also transferred well to
ImageNet, achieving competitive accuracy.

Figure 1 shows the accuracy over time. As you can see, it improves significantly. The final
architecture found by our method has an interesting structure with multiple skip connections.

## 4.1 Comparison with Baselines

We compared our approach against manually designed architectures and other NAS methods. Our
method achieved superior performance while requiring less computational resources.

# 5. Discussion

The results demonstrate that RL can effectively search for neural architectures. One limitation
is the computational cost - searching for architectures required significant GPU resources.
Future work could explore more efficient search methods.

Our approach has implications for AutoML and could make deep learning more accessible. It shows
that automated methods can match or exceed human-designed architectures.

# 6. Conclusion

We presented a method for neural architecture search using reinforcement learning. The approach
successfully discovered high-performing architectures that outperformed manual designs.
"""

print("="*80)
print("TESTING SECTION PARSER")
print("="*80)
print()

print("First 15 lines of SAMPLE_PAPER:")
print("-"*80)
for i, line in enumerate(SAMPLE_PAPER.split('\n')[:15], 1):
    print(f"{i:2}: {repr(line)}")
print("-"*80)
print()

analyzer = SectionAnalyzer()
sections = analyzer.parse_markdown(SAMPLE_PAPER)

print(f"Total sections parsed: {len(sections)}")
print()

if len(sections) == 0:
    print("❌ ERROR: No sections found!")
    print()
    print("This means the parser is not finding numbered sections.")
    print("Check that:")
    print("  1. The SectionAnalyzer code has been updated")
    print("  2. The Python files have been reloaded")
else:
    print("✅ SUCCESS: Sections found!")
    print()
    for i, section in enumerate(sections, 1):
        print(f"{i}. Section {section.section_number}: {section.title}")
        print(f"   Level: {section.level}")
        print(f"   Lines: {section.line_start}-{section.line_end}")
        print(f"   Content: {len(section.content)} chars")
        print(f"   Subsections: {section.subsections}")
        print()
