# MCM 2024 Problem A — Resource Availability and Sex Ratios

Problem A of MCM/ICM 2024.
See: https://www.comap.com/contests/mcm-icm

## Solving with MathModel Toolkit

```python
from mathmodel import Pipeline, PipelineConfig

config = PipelineConfig(
    engine="latex",
    contest_type="mcm",
    language="en",
    output_dir="./output_mcm2024a",
)

pipe = Pipeline(config=config)
pipe.run(
    problem="2024_MCM_Problem_A.pdf",
    data=["data.xlsx"],
)
```
