"""F-RV6 干扰 watcher（PLAN-014 T-09）：3s 采样 auto.exe 实例数，落谱文件。"""
import subprocess, time, sys
out = sys.argv[1]
t0 = time.time()
with open(out, "w", encoding="utf-8") as f:
    while True:
        try:
            n = subprocess.run(["tasklist"], capture_output=True, text=True
                               ).stdout.lower().count("auto.exe")
        except OSError:
            n = -1
        f.write(f"{round(time.time()-t0,1)}\t{n}\n")
        f.flush()
        time.sleep(3)
