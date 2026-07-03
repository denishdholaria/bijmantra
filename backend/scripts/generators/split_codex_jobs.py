import os
from pathlib import Path

SOURCE_FILE = "docs/development/reevu/reevu-codex10-recovery-job-cards-v2.md"
OUTPUT_DIR = Path("docs/development/platoons/E_Codex_Recovery")

def split_jobs():
    if not os.path.exists(SOURCE_FILE):
        print(f"Error: {SOURCE_FILE} not found.")
        return

    with open(SOURCE_FILE, 'r') as f:
        lines = f.readlines()

    common_prompt = []
    in_common = False
    
    jobs = {}
    current_job = None
    in_job = False

    for line in lines:
        if "**================ BEGIN COMMON PROMPT ================**" in line:
            in_common = True
            continue
        elif "**================ END COMMON PROMPT ================**" in line:
            in_common = False
            continue
            
        if in_common:
            common_prompt.append(line)
            continue

        if "**================ BEGIN JOB" in line:
            # Extract job id like C01
            parts = line.strip().split()
            current_job = parts[3]
            jobs[current_job] = []
            in_job = True
            continue
        elif "**================ END JOB" in line:
            in_job = False
            current_job = None
            continue

        if in_job and current_job:
            jobs[current_job].append(line)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    common_text = "".join(common_prompt).strip()

    count = 0
    for job_id, job_lines in jobs.items():
        job_text = "".join(job_lines).strip()
        
        full_payload = f"# REEVU CODEX RECOVERY JOB: {job_id}\n\n"
        full_payload += "## 1. BASE INSTRUCTIONS (COMMON PROMPT)\n"
        full_payload += common_text + "\n\n"
        full_payload += "-" * 50 + "\n\n"
        full_payload += f"## 2. YOUR SPECIFIC MISSION: JOB {job_id}\n"
        full_payload += job_text + "\n"

        out_path = OUTPUT_DIR / f"{job_id}-prompt.txt"
        with open(out_path, "w") as out_f:
            out_f.write(full_payload)
        count += 1

    print(f"✅ Generated {count} Codex Recovery Prompts in {OUTPUT_DIR}")

if __name__ == "__main__":
    split_jobs()
