import { useState, useEffect } from 'react';
import { Download, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';

export default function History() {
  const [jobs, setJobs] = useState([]);

  // For this mock we just use a static list or an empty state since backend history endpoint isn't fully implemented to fetch all jobs
  // But ideally we'd fetch from /api/jobs
  
  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <header>
        <h1 className="text-3xl font-extrabold mb-2">Generation History</h1>
        <p className="text-gray-400">View and download your past video batches.</p>
      </header>

      <div className="bg-dark-800 rounded-xl border border-dark-700 shadow-xl overflow-x-auto w-full">
        {jobs.length === 0 ? (
          <div className="p-8 md:p-12 text-center text-gray-400 flex flex-col items-center">
            <div className="w-16 h-16 bg-dark-700 rounded-full flex items-center justify-center mb-4">
              <span className="text-2xl">📭</span>
            </div>
            <h3 className="text-lg font-medium text-white mb-1">No history yet</h3>
            <p className="text-sm md:text-base">Your generated batches will appear here.</p>
          </div>
        ) : (
          <table className="w-full text-sm text-left min-w-[600px]">
            <thead className="text-xs text-gray-300 uppercase bg-dark-900 border-b border-dark-700">
              <tr>
                <th className="px-4 py-3 md:px-6 md:py-4">Session ID</th>
                <th className="px-4 py-3 md:px-6 md:py-4">Status</th>
                <th className="px-4 py-3 md:px-6 md:py-4">Videos</th>
                <th className="px-4 py-3 md:px-6 md:py-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map(job => (
                <tr key={job.session_id} className="border-b border-dark-700 hover:bg-dark-700/50 transition-colors">
                  <td className="px-4 py-3 md:px-6 md:py-4 font-mono text-gray-300 text-xs md:text-sm">{job.session_id.substring(0, 8)}...</td>
                  <td className="px-4 py-3 md:px-6 md:py-4">
                    <div className="flex items-center gap-1 md:gap-2">
                      {job.status === 'Completed' && <CheckCircle className="w-4 h-4 text-green-500" />}
                      {job.status === 'Interrupted' && <AlertTriangle className="w-4 h-4 text-yellow-500" />}
                      {job.status === 'Failed' && <XCircle className="w-4 h-4 text-red-500" />}
                      <span className={
                        job.status === 'Completed' ? 'text-green-500' :
                        job.status === 'Interrupted' ? 'text-yellow-500' :
                        'text-red-500'
                      }>{job.status}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 md:px-6 md:py-4 text-gray-300">{job.completed_so_far} / {job.total_expected}</td>
                  <td className="px-4 py-3 md:px-6 md:py-4 text-right">
                    {(job.status === 'Completed' || job.status === 'Interrupted') && (
                      <button 
                        onClick={() => window.location.href = `http://localhost:8000/api/download/${job.session_id}`}
                        className="inline-flex items-center gap-1 md:gap-2 text-brand-400 hover:text-brand-300 transition-colors bg-brand-500/10 hover:bg-brand-500/20 px-3 py-1.5 md:px-4 md:py-2 rounded-lg"
                      >
                        <Download className="w-4 h-4" /> <span className="hidden md:inline">Download</span>
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
