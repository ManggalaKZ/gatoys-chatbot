import json
from datetime import datetime
from zoneinfo import ZoneInfo
from core.config import METRICS_FILE
import traceback



def export_metrics_for_thesis():
    """
    Export metrics dalam format yang mudah untuk analisis skripsi
    """
    try:
        # Load metrics
        with open(METRICS_FILE, 'r', encoding='utf-8') as f:
            metrics = json.load(f)
        
        # Load Q&A logs
        qa_log_file = "result_response_data.json"
        with open(qa_log_file, 'r', encoding='utf-8') as f:
            qa_logs = json.load(f)
        
        # Generate report
        output = []
        output.append("="*80)
        output.append("CHATBOT PERFORMANCE METRICS - UNTUK SKRIPSI")
        output.append("="*80)
        output.append("")
        
        output.append("1. STATISTIK UMUM")
        output.append("-" * 80)
        output.append(f"Total Queries                : {metrics['total_queries']}")
        output.append(f"Average Response Time        : {metrics['avg_response_time']:.3f} seconds")
        output.append(f"Total Q&A Logs               : {len(qa_logs)}")
        output.append("")
        
        output.append("2. DISTRIBUSI JENIS QUERY")
        output.append("-" * 80)
        
        # Sort by count
        sorted_types = sorted(metrics['query_types'].items(), key=lambda x: x[1], reverse=True)
        
        for qtype, count in sorted_types:
            percentage = (count / max(metrics['total_queries'], 1)) * 100
            output.append(f"{qtype:30s}: {count:4d} ({percentage:5.1f}%)")
        output.append("")
        
        output.append("3. SESSION ANALYSIS")
        output.append("-" * 80)
        sessions = metrics['sessions']
        output.append(f"Total Sessions               : {len(sessions)}")
        
        if sessions:
            total_duration = sum(s['duration_seconds'] for s in sessions)
            avg_duration = total_duration / len(sessions)
            total_session_queries = sum(s['queries_in_session'] for s in sessions)
            
            output.append(f"Total Duration (All Sessions): {total_duration:.1f} seconds")
            output.append(f"Average Session Duration     : {avg_duration:.1f} seconds")
            output.append(f"Average Queries per Session  : {total_session_queries/len(sessions):.1f}")
            output.append("")
            
            output.append("Recent Sessions:")
            for session in sessions[-5:]:
                output.append(f"  Session #{session['session_id']}: "
                            f"{session['queries_in_session']} queries, "
                            f"{session['duration_seconds']:.1f}s")
        
        output.append("")
        output.append("4. SAMPLE Q&A (Latest 5)")
        output.append("-" * 80)
        
        for qa in qa_logs[-5:]:
            output.append(f"Q{qa['query_id']}: {qa['question'][:60]}...")
            output.append(f"   Type: {qa['query_type']} | Time: {qa['response_time_seconds']}s")
            output.append(f"   A: {qa['answer'][:100]}...")
            output.append("")
        
        output.append("="*80)
        output.append(f"Report Generated: {datetime.now(ZoneInfo("Asia/Jakarta")).isoformat()}")
        output.append(f"Data Files: {METRICS_FILE}, {qa_log_file}")
        output.append("="*80)
        
        report = "\n".join(output)
        
        # Save to file
        report_file = "thesis_metrics_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(report)
        print(f"\n[SUCCESS] Report exported to {report_file}")
        
        return report
        
    except Exception as e:
        print(f"[ERROR] Failed to export metrics: {e}")
        traceback.print_exc()
        return None


