.PHONY: test lint experiments all p2-corpus p2-capture p2-census p2-status p3 p2b p4 p5 p6 p7
test:
	pytest -q
lint:
	python tools/lint_findings.py
experiments:
	python experiments/a01_rate_vs_draft_quality.py && python experiments/a02_attestation.py && python experiments/a03_rank_flip_synthetic.py
all: test lint experiments
p2-corpus:
	python -m amber.real.capture corpus --text ../tokenizer-lab/data/mix_docs50_wiki50.txt
p2-capture:
	python -m amber.real.capture run --arm cpu_fp32 --arm cpu_fp32_rep --arm cuda_bf16_b1 --arm cuda_bf16_b1_rep --arm cuda_bf16_b8 --arm cuda_fp16_b1 --arm cuda_fp32_b1 --arm cuda_int8_b1 --arm cuda_nf4_b1
p2-status:
	python -m amber.real.capture status
p2-census:
	python experiments/p2_rank_census.py

p3:
	python experiments/p3_rac_rate.py
p2b:
	python experiments/p2b_escape_robustness.py

p4:
	python experiments/p4_real_archive.py encode && python experiments/p4_real_archive.py decode --arm cuda_fp32 --arm cuda_bf16 --arm cuda_fp16 && python experiments/p4_real_archive.py decode --arm cpu_fp32 --n-prompts 24 && python experiments/p4_real_archive.py report

p5:
	python experiments/p5_binformat.py encode && python experiments/p5_binformat.py decode && python experiments/p5_binformat.py report

p6:
	python experiments/p6_sessions.py encode && python experiments/p6_sessions.py decode && python experiments/p6_sessions.py report

p7:
	python experiments/p7_longhorizon.py generate && python experiments/p7_longhorizon.py encode && python experiments/p7_longhorizon.py decode && python experiments/p7_longhorizon.py report
