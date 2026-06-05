import { useState, useEffect } from 'react';
import axios from 'axios';
import { Download, CheckCircle, AlertTriangle, XCircle, FileVideo } from 'lucide-react';
import { useAuth } from '../AuthContext';

export default function History() {
  const { currentUser, login } = useAuth();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (currentUser?.email) {
      setLoading(true);
      axios.get(`/api/hf/jobs?email=${currentUser.email}`)
        .then(res => {
          setJobs(res.data.jobs || []);
        })
        .catch(err => {
          console.error("Error loading history", err);
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, [currentUser]);

  if (!currentUser) {
    return (
      <div className="space-y-8 animate-in fade-in duration-500 max-w-2xl mx-auto text-center py-12">
        <header className="space-y-2">
          <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white">Generation History</h1>
          <p className="text-gray-500 dark:text-gray-400">View and download your past video batches.</p>
        </header>

        <div className="bg-white dark:bg-dark-800 p-8 md:p-12 rounded-2xl border border-gray-200 dark:border-dark-700 shadow-xl flex flex-col items-center">
          <div className="w-16 h-16 bg-brand-500/10 text-brand-500 rounded-full flex items-center justify-center mb-6 border border-brand-500/20">
            <FileVideo className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-bold text-gray-800 dark:text-white mb-2">Login Required</h3>
          <p className="text-gray-500 dark:text-gray-400 text-sm mb-6 max-w-sm">
            Please log in to your account to view your past quiz video generations and download history.
          </p>
          <button 
            onClick={login}
            className="bg-brand-600 hover:bg-brand-500 text-white px-6 py-2.5 rounded-xl font-bold transition-all shadow-lg shadow-brand-500/20"
          >
            Login / Sign In
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <header>
        <h1 className="text-3xl font-extrabold mb-2 text-gray-900 dark:text-white">Generation History</h1>
        <p className="text-gray-500 dark:text-gray-400">View and download your past video batches.</p>
      </header>

      <div className="bg-white dark:bg-dark-800 rounded-xl border border-gray-200 dark:border-dark-700 shadow-xl overflow-x-auto w-full">
        {loading ? (
          <div className="p-12 text-center text-gray-500 dark:text-gray-400">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-500 mx-auto mb-4"></div>
            Loading your projects history...
          </div>
        ) : jobs.length === 0 ? (
          <div className="p-8 md:p-12 text-center text-gray-500 dark:text-gray-400 flex flex-col items-center">
            <div className="w-16 h-16 bg-gray-100 dark:bg-dark-700 rounded-full flex items-center justify-center mb-4">
              <span className="text-2xl">📭</span>
            </div>
            <h3 className="text-lg font-bold text-gray-800 dark:text-white mb-1">No history yet</h3>
            <p className="text-sm">Your generated video batches will appear here.</p>
          </div>
        ) : (
          <table className="w-full text-sm text-left min-w-[600px]">
            <thead className="text-xs text-gray-600 dark:text-gray-300 uppercase bg-gray-50 dark:bg-dark-900 border-b border-gray-200 dark:border-dark-700">
              <tr>
                <th className="px-4 py-3 md:px-6 md:py-4">Session ID</th>
                <th className="px-4 py-3 md:px-6 md:py-4">Status</th>
                <th className="px-4 py-3 md:px-6 md:py-4">Videos</th>
                <th className="px-4 py-3 md:px-6 md:py-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map(job => (
                <tr key={job.session_id} className="border-b border-gray-200 dark:border-dark-700 hover:bg-gray-50 dark:hover:bg-dark-700/50 transition-colors">
                  <td className="px-4 py-3 md:px-6 md:py-4 font-mono text-gray-700 dark:text-gray-300 text-xs md:text-sm">{job.session_id.substring(0, 8)}...</td>
                  <td className="px-4 py-3 md:px-6 md:py-4">
                    <div className="flex items-center gap-1 md:gap-2">
                      {job.status === 'Completed' && <CheckCircle className="w-4 h-4 text-green-500" />}
                      {job.status === 'Interrupted' && <AlertTriangle className="w-4 h-4 text-yellow-500" />}
                      {job.status === 'Failed' && <XCircle className="w-4 h-4 text-red-500" />}
                      {job.status === 'Processing' && <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-brand-500"></div>}
                      <span className={
                        job.status === 'Completed' ? 'text-green-500 font-medium' :
                        job.status === 'Interrupted' ? 'text-yellow-500 font-medium' :
                        job.status === 'Processing' ? 'text-brand-500 font-medium' :
                        'text-red-500 font-medium'
                      }>{job.status}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 md:px-6 md:py-4 text-gray-700 dark:text-gray-300 font-medium">{job.completed_so_far} / {job.total_expected}</td>
                  <td className="px-4 py-3 md:px-6 md:py-4 text-right">
                    {(job.status === 'Completed' || job.status === 'Interrupted') && (
                      <button 
                        onClick={() => window.location.href = `/api/hf/download/${job.session_id}`}
                        className="inline-flex items-center gap-1 md:gap-2 text-brand-600 dark:text-brand-400 hover:text-brand-700 dark:hover:text-brand-300 transition-colors bg-brand-500/10 hover:bg-brand-500/20 px-3 py-1.5 md:px-4 md:py-2 rounded-lg"
                      >
                        <Download className="w-4 h-4" /> <span className="hidden md:inline">Download ZIP</span>
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
