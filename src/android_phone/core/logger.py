import os
import json
import time
import random
import shutil
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class TaskLogger:
    def __init__(self, log_dir: str = ".log", expire_days: int = 10):
        self.log_dir = Path(log_dir)
        self.expire_days = expire_days
        self._init_log_dir()

    def _init_log_dir(self):
        """初始化日志目录"""
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _cleanup_expired_logs(self):
        """清理过期的日志文件"""
        if not self.log_dir.exists():
            return

        now = time.time()
        for file_path in self.log_dir.glob("*.jsonl"):
            if now - file_path.stat().st_mtime > self.expire_days * 86400:
                try:
                    file_path.unlink()
                except Exception:
                    pass

    def generate_task_id(self) -> str:
        """生成任务ID: 时间戳 + 随机整数"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_int = random.randint(1000, 9999)
        return f"{timestamp}_{random_int}"

    def _get_today_log_file(self) -> Path:
        """获取今天的日志文件路径"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"{today}.jsonl"

    def log_task_start(self, task_id: str, goal: str) -> Dict[str, Any]:
        """记录任务开始"""
        self._cleanup_expired_logs()

        log_entry = {
            "task_id": task_id,
            "event": "task_start",
            "timestamp": datetime.now().isoformat(),
            "goal": goal
        }

        with open(self._get_today_log_file(), "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        return log_entry

    def log_step(
        self,
        task_id: str,
        step: int,
        instruction: str,
        image_b64: str,
        model_response: Dict[str, Any],
        usage: Dict[str, Any],
        action: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """记录每一步的模型调用"""
        log_entry = {
            "task_id": task_id,
            "event": "step",
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "instruction": instruction,
            "image_b64_length": len(image_b64) if image_b64 else 0,
            "model_input": {
                "instruction": instruction,
                "image_length": len(image_b64) if image_b64 else 0
            },
            "model_output": {
                "thought": model_response.get("thought", ""),
                "raw_content": model_response.get("raw_content", "")[:500] if model_response.get("raw_content") else "",
                "action_type": model_response.get("action_parsed", {}).get("type", "") if model_response.get("action_parsed") else ""
            },
            "token_usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            },
            "action_executed": action
        }

        with open(self._get_today_log_file(), "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        return log_entry

    def log_task_end(
        self,
        task_id: str,
        result: str,
        total_usage: Dict[str, int],
        steps_count: int
    ) -> Dict[str, Any]:
        """记录任务结束"""
        log_entry = {
            "task_id": task_id,
            "event": "task_end",
            "timestamp": datetime.now().isoformat(),
            "result": result,
            "total_token_usage": total_usage,
            "total_steps": steps_count
        }

        with open(self._get_today_log_file(), "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        return log_entry

    def get_task_logs(self, task_id: str) -> list:
        """获取指定任务的日志"""
        logs = []
        for log_file in self.log_dir.glob("*.jsonl"):
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if entry.get("task_id") == task_id:
                            logs.append(entry)
                    except json.JSONDecodeError:
                        continue
        return sorted(logs, key=lambda x: x.get("timestamp", ""))

    def list_recent_tasks(self, limit: int = 20) -> list:
        """列出最近的任务"""
        tasks = []
        seen = set()

        for log_file in sorted(self.log_dir.glob("*.jsonl"), reverse=True):
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if entry.get("event") == "task_start" and entry["task_id"] not in seen:
                            tasks.append(entry)
                            seen.add(entry["task_id"])
                            if len(tasks) >= limit:
                                return tasks
                    except json.JSONDecodeError:
                        continue

        return tasks
