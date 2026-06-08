 
# ============================================================
# METRICS TRACKER (REFACTORED - untuk analisis skripsi)
# ============================================================
from langchain.docstore.document import Document
from typing import List, Dict
from datetime import datetime
import time
from pathlib import Path
import json
import threading 
from zoneinfo import ZoneInfo


class MetricsTracker:
    """
    Track chatbot performance metrics untuk skripsi
    
    METRICS YANG DI-TRACK:
    1. Total queries
    2. Query type distribution
    3. Average response time
    4. Detailed Q&A logs (result_response_data.json)
    5. Session tracking
    """
    
    def __init__(self, enabled: bool = True, metrics_file: str = "chatbot_metrics.json", 
                 qa_log_file: str = "result_response_data.json"):
        self.enabled = enabled
        self.metrics_file = metrics_file
        self.qa_log_file = qa_log_file
        self.lock = threading.Lock() 
        
        # Main metrics
        self.metrics = {
            "total_queries": 0,
            "avg_response_time": 0.0,
            "query_types": {},
            "sessions": [],
            "start_time": datetime.now(ZoneInfo("Asia/Jakarta")).isoformat(),
            "last_updated": datetime.now(ZoneInfo("Asia/Jakarta")).isoformat()

        }
        
        # Q&A detailed logs
        self.qa_logs = []
        
        # Session tracking
        self.session_start = time.time()
        self.current_session_queries = 0
        
        # Load existing data
        self.load_metrics()
        self.load_qa_logs()
    
    def load_metrics(self):
        """Load existing metrics"""
        try:
            if Path(self.metrics_file).exists():
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    # Merge dengan current session
                    self.metrics["total_queries"] = saved.get("total_queries", 0)
                    self.metrics["avg_response_time"] = saved.get("avg_response_time", 0.0)
                    self.metrics["query_types"] = saved.get("query_types", {})
                    self.metrics["sessions"] = saved.get("sessions", [])
                print(f"[METRICS] Loaded existing metrics: {self.metrics['total_queries']} total queries")
        except Exception as e:
            print(f"[WARN] Could not load metrics: {e}")
    
    def load_qa_logs(self):
        """Load existing Q&A logs"""
        try:
            if Path(self.qa_log_file).exists():
                with open(self.qa_log_file, 'r', encoding='utf-8') as f:
                    self.qa_logs = json.load(f)
                print(f"[METRICS] Loaded {len(self.qa_logs)} Q&A logs")
        except Exception as e:
            print(f"[WARN] Could not load Q&A logs: {e}")
    
    def log_query(self, question: str, answer: str, response_time: float, 
                  query_type: str, sources: List = None):
        if not self.enabled:
            return
        
        # Gunakan Lock saat memodifikasi data shared memory
        with self.lock:
            # Update total queries
            self.metrics["total_queries"] += 1
            self.current_session_queries += 1
            
            # Update average response time
            n = self.metrics["total_queries"]
            self.metrics["avg_response_time"] = (
                (self.metrics["avg_response_time"] * (n - 1) + response_time) / n
            )
            
            # Track query types
            if query_type not in self.metrics["query_types"]:
                self.metrics["query_types"][query_type] = 0
            self.metrics["query_types"][query_type] += 1
            
            self.metrics["last_updated"] = datetime.now(ZoneInfo("Asia/Jakarta")).isoformat()

        
        # Create detailed Q&A log entry
        qa_entry = {
            "query_id": len(self.qa_logs) + 1,
            "timestamp": datetime.now(ZoneInfo("Asia/Jakarta")).isoformat(),
            "question": question,
            "answer": answer,
            "query_type": query_type,
            "response_time_seconds": round(response_time, 3)
        }
        
        # Add source information if available
        if sources:
            qa_entry["sources"] = []
            for i, doc in enumerate(sources[:5], 1):  # Max 5 sources
                source_info = {
                    "rank": i,
                    "type": doc.metadata.get('type', 'unknown')
                }
                
                if doc.metadata.get('type') == 'product':
                    source_info.update({
                        "product_name": doc.metadata.get('name', 'N/A'),
                        "product_id": doc.metadata.get('product_id', 'N/A'),
                        "price": doc.metadata.get('price', 0)
                    })
                else:
                    source_info["title"] = doc.metadata.get('title', 'Store Info')
                
                qa_entry["sources"].append(source_info)
        
        # Add to logs
        self.qa_logs.append(qa_entry)
        
        # Pindahkan save logic ke luar lock atau biarkan di dalam jika save cepat
        should_save = self.metrics["total_queries"] % 5 == 0
        
        # Auto-save periodically (every 5 queries)
        # Save di luar lock modifikasi data, tapi save_all punya lock sendiri
        if should_save:
            self.save_all()
    
    def end_session(self):
        """End current session and save all data"""
        session_duration = time.time() - self.session_start
        
        session_data = {
            "session_id": len(self.metrics["sessions"]) + 1,
            "start_time": datetime.fromtimestamp(self.session_start).isoformat(),
            "end_time": datetime.now(ZoneInfo("Asia/Jakarta")).isoformat(),
            "duration_seconds": round(session_duration, 2),
            "queries_in_session": self.current_session_queries
        }
        
        self.metrics["sessions"].append(session_data)
        self.save_all()
        
        print(f"\n[SESSION END] Duration: {session_duration:.1f}s | Queries: {self.current_session_queries}")
    
    def save_all(self):
        """Save both metrics and Q&A logs (Thread-Safe)"""
        # Lock file I/O agar tidak ada 2 thread menulis file bersamaan
        with self.lock:
            try:
                with open(self.metrics_file, 'w', encoding='utf-8') as f:
                    json.dump(self.metrics, f, indent=2, ensure_ascii=False)
                
                with open(self.qa_log_file, 'w', encoding='utf-8') as f:
                    json.dump(self.qa_logs, f, indent=2, ensure_ascii=False)
                    
            except Exception as e:
                print(f"[ERROR] Could not save metrics: {e}")
    
    def get_summary(self) -> str:
        """Get formatted metrics summary"""
        m = self.metrics
        
        summary = f"""
╔═══════════════════════════════════════════════════════════╗
║            CHATBOT PERFORMANCE METRICS                    ║
╠═══════════════════════════════════════════════════════════╣
║ Total Queries         : {m['total_queries']:>6}                           ║
║ Average Response Time : {m['avg_response_time']:>6.3f}s                           ║
║ Total Sessions        : {len(m['sessions']):>6}                           ║
║                                                           ║
║ Query Type Distribution:                                  ║"""
        
        # Sort query types by count (descending)
        sorted_types = sorted(m["query_types"].items(), key=lambda x: x[1], reverse=True)
        
        for qtype, count in sorted_types:
            percentage = (count / max(m["total_queries"], 1)) * 100
            summary += f"\n║   {qtype:25s}: {count:>4} ({percentage:5.1f}%)            ║"
        
        summary += "\n║                                                           ║"
        summary += f"\n║ Last Updated: {m['last_updated'][:19]:>38}     ║"
        summary += "\n╚═══════════════════════════════════════════════════════════╝"
        
        return summary
    
    def get_session_summary(self) -> str:
        """Get summary of all sessions"""
        if not self.metrics["sessions"]:
            return "No sessions recorded yet."
        
        sessions = self.metrics["sessions"]
        total_duration = sum(s["duration_seconds"] for s in sessions)
        avg_duration = total_duration / len(sessions)
        total_queries = sum(s["queries_in_session"] for s in sessions)
        
        summary = f"""
╔═══════════════════════════════════════════════════════════╗
║                   SESSION SUMMARY                         ║
╠═══════════════════════════════════════════════════════════╣
║ Total Sessions        : {len(sessions):>6}                          ║
║ Total Queries (All)   : {total_queries:>6}                          ║
║ Avg Queries/Session   : {total_queries/len(sessions):>6.1f}                      ║
║ Avg Session Duration  : {avg_duration:>6.1f}s                      ║
║                                                           ║
║ Recent Sessions:                                          ║"""
        
        # Show last 5 sessions
        for session in sessions[-5:]:
            session_id = session["session_id"]
            queries = session["queries_in_session"]
            duration = session["duration_seconds"]
            summary += f"\n║   Session #{session_id:02d}: {queries:>3} queries in {duration:>6.1f}s          ║"
        
        summary += "\n╚═══════════════════════════════════════════════════════════╝"
        
        return summary
