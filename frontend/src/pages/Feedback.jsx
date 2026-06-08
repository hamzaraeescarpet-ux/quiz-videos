import { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../AuthContext';
import { MessageSquare, Star, Send, Trash2, Calendar, Mail, AlertTriangle, Users, Download, Copy, Check } from 'lucide-react';

export default function Feedback() {
  const { currentUser } = useAuth();
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  // Admin states
  const [feedbacks, setFeedbacks] = useState([]);
  const [registeredUsers, setRegisteredUsers] = useState([]);
  const [activeTab, setActiveTab] = useState('feedbacks'); // 'feedbacks' or 'emails'
  const [copied, setCopied] = useState(false);

  const isAdmin = currentUser && ['hamzaraeescarpet@gmail.com', 'hamzarais2023@gmail.com'].includes(currentUser.email);

  useEffect(() => {
    if (isAdmin) {
      // Fetch feedbacks
      axios.get(`/api/hf/admin/feedbacks?email=${currentUser.email}`)
        .then(res => setFeedbacks(res.data.feedbacks || []))
        .catch(err => console.error("Error loading feedbacks", err));

      // Fetch registered marketing emails
      axios.get(`/api/hf/admin/users?email=${currentUser.email}`)
        .then(res => setRegisteredUsers(res.data.users || []))
        .catch(err => console.error("Error loading users", err));
    }
  }, [isAdmin, currentUser]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!currentUser) {
      setErrorMsg("Please login to submit feedback!");
      return;
    }
    if (!comment.trim()) {
      setErrorMsg("Please enter a comment!");
      return;
    }

    setLoading(true);
    setErrorMsg('');
    try {
      await axios.post('/api/hf/feedback', {
        email: currentUser.email,
        rating,
        comment
      });
      setSuccess(true);
      setComment('');
      setRating(5);
      
      if (isAdmin) {
        const res = await axios.get(`/api/hf/admin/feedbacks?email=${currentUser.email}`);
        setFeedbacks(res.data.feedbacks || []);
      }
    } catch (err) {
      console.error(err);
      setErrorMsg("Failed to submit feedback. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Copy all emails helper
  const copyAllEmails = () => {
    const emailList = registeredUsers.map(u => u.email).join(', ');
    navigator.clipboard.writeText(emailList);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Download CSV helper
  const downloadCSV = () => {
    const headers = 'ID,Email,Videos Generated,Is Premium\n';
    const csvContent = registeredUsers.map(u => `${u.id},${u.email},${u.videos_count},${u.is_premium}`).join('\n');
    const blob = new Blob([headers + csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', 'quizviral_users_marketing.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500 max-w-4xl mx-auto">
      <header className="text-center space-y-2">
        <h1 className="text-3xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-brand-400 to-brand-600">
          User Feedback & Suggestions
        </h1>
        <p className="text-gray-400">Your feedback helps us make QuizViral AI the ultimate video creation platform.</p>
      </header>

      <div className="grid grid-cols-1 gap-8">
        {/* User Submission Form */}
        <section className="bg-dark-800 p-6 md:p-8 rounded-2xl border border-dark-700 shadow-xl space-y-6">
          <h2 className="text-xl font-bold flex items-center gap-2 text-brand-300">
            <MessageSquare className="w-5 h-5 text-brand-500" /> Share Your Thoughts
          </h2>

          {success ? (
            <div className="bg-green-500/10 border border-green-500/30 text-green-400 p-4 rounded-xl text-center space-y-3">
              <span className="text-3xl">🎉</span>
              <p className="font-bold">Thank you for your feedback!</p>
              <p className="text-xs text-gray-400">We appreciate your support and will work on your suggestions.</p>
              <button 
                onClick={() => setSuccess(false)}
                className="mt-2 bg-dark-700 hover:bg-dark-600 px-4 py-2 rounded-lg text-sm font-semibold transition-colors text-white"
              >
                Submit another response
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              {errorMsg && (
                <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg text-sm flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" /> {errorMsg}
                </div>
              )}

              {/* Rating Selector */}
              <div>
                <label className="block text-sm font-semibold text-gray-300 mb-2">How would you rate your experience?</label>
                <div className="flex items-center gap-2">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => setRating(star)}
                      className="p-1 transition-transform transform hover:scale-125 focus:outline-none"
                    >
                      <Star className={`w-8 h-8 ${rating >= star ? 'text-yellow-500 fill-current' : 'text-gray-600'}`} />
                    </button>
                  ))}
                </div>
              </div>

              {/* Suggestions Box */}
              <div>
                <label className="block text-sm font-semibold text-gray-300 mb-2">Your Suggestions, Questions or Bug Reports</label>
                <textarea
                  rows="4"
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="Tell us what you like or what we can improve..."
                  className="w-full bg-dark-900 border border-dark-600 rounded-xl px-4 py-3 focus:ring-2 focus:ring-brand-500 outline-none text-sm placeholder-gray-500 text-gray-200"
                ></textarea>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 px-6 rounded-xl bg-gradient-to-r from-brand-600 to-brand-400 text-white font-bold hover:from-brand-500 hover:to-brand-300 transition-all flex items-center justify-center gap-2 shadow-lg shadow-brand-500/25 disabled:opacity-50"
              >
                {loading ? 'Submitting...' : (
                  <>
                    <Send className="w-4 h-4" /> Submit Feedback
                  </>
                )}
              </button>
            </form>
          )}
        </section>

        {/* Administrator Dashboard Board (Visible only to hamzaraeescarpet@gmail.com) */}
        {isAdmin && (
          <section className="bg-dark-800 p-6 md:p-8 rounded-2xl border border-dark-700 shadow-xl space-y-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center border-b border-dark-700 pb-4 gap-4">
              <h2 className="text-xl font-extrabold text-brand-300 flex items-center gap-2">
                👑 Admin Management Board
              </h2>
              
              {/* Tab Selector */}
              <div className="flex bg-dark-900 p-1 rounded-lg border border-dark-700">
                <button
                  onClick={() => setActiveTab('feedbacks')}
                  className={`px-4 py-1.5 rounded-md text-xs font-bold transition-all ${activeTab === 'feedbacks' ? 'bg-brand-600 text-white shadow' : 'text-gray-400 hover:text-white'}`}
                >
                  Feedbacks ({feedbacks.length})
                </button>
                <button
                  onClick={() => setActiveTab('emails')}
                  className={`px-4 py-1.5 rounded-md text-xs font-bold transition-all ${activeTab === 'emails' ? 'bg-brand-600 text-white shadow' : 'text-gray-400 hover:text-white'}`}
                >
                  Marketing Emails ({registeredUsers.length})
                </button>
              </div>
            </div>

            {/* TAB 1: USER FEEDBACKS */}
            {activeTab === 'feedbacks' && (
              <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2">
                {feedbacks.length > 0 ? feedbacks.map((item) => (
                  <div key={item.id} className="bg-dark-900/50 p-4 rounded-xl border border-dark-700 space-y-3 relative hover:border-dark-600 transition-all">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <Mail className="w-4 h-4 text-brand-400" />
                        <span className="text-sm font-bold text-gray-200 break-all">{item.email}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-gray-400">
                        <div className="flex items-center gap-1">
                          <Calendar className="w-3.5 h-3.5" />
                          {item.submitted_at}
                        </div>
                        <div className="flex items-center">
                          {[1, 2, 3, 4, 5].map((star) => (
                            <Star key={star} className={`w-3.5 h-3.5 ${item.rating >= star ? 'text-yellow-500 fill-current' : 'text-gray-700'}`} />
                          ))}
                        </div>
                      </div>
                    </div>
                    <p className="text-gray-300 text-sm bg-dark-950 p-3 rounded-lg border border-dark-800 leading-relaxed break-words whitespace-pre-wrap">
                      {item.comment}
                    </p>
                  </div>
                )) : (
                  <p className="text-gray-500 text-sm text-center py-6">No feedbacks submitted yet.</p>
                )}
              </div>
            )}

            {/* TAB 2: REGISTERED EMAILS (MARKETING) */}
            {activeTab === 'emails' && (
              <div className="space-y-6">
                {/* Actions Toolbar */}
                <div className="flex flex-wrap items-center gap-3">
                  <button
                    onClick={copyAllEmails}
                    className="bg-dark-700 hover:bg-dark-600 text-white font-bold text-xs px-4 py-2.5 rounded-lg border border-dark-600 flex items-center gap-2 transition-all"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5 text-brand-400" />}
                    {copied ? 'Copied to Clipboard!' : 'Copy All Emails'}
                  </button>
                  <button
                    onClick={downloadCSV}
                    className="bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs px-4 py-2.5 rounded-lg flex items-center gap-2 transition-all shadow-md shadow-brand-500/10"
                  >
                    <Download className="w-3.5 h-3.5" /> Download Users CSV
                  </button>
                </div>

                {/* Table Grid */}
                <div className="overflow-x-auto rounded-lg border border-dark-700 max-h-[400px] overflow-y-auto">
                  <table className="w-full text-sm text-left">
                    <thead className="text-xs uppercase bg-dark-900 text-gray-300 sticky top-0">
                      <tr>
                        <th className="px-4 py-3">ID</th>
                        <th className="px-4 py-3">Email Address</th>
                        <th className="px-4 py-3 text-center">Videos Made</th>
                        <th className="px-4 py-3 text-center">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-dark-700/60 bg-dark-950/40">
                      {registeredUsers.length > 0 ? registeredUsers.map((user) => (
                        <tr key={user.id} className="hover:bg-dark-900/30 transition-colors">
                          <td className="px-4 py-3 font-mono text-xs text-gray-500">#{user.id}</td>
                          <td className="px-4 py-3 font-medium text-gray-200">{user.email}</td>
                          <td className="px-4 py-3 text-center text-brand-400 font-bold font-mono">{user.videos_count}</td>
                          <td className="px-4 py-3 text-center">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${user.is_premium ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-gray-700/20 text-gray-400'}`}>
                              {user.is_premium ? 'Premium' : 'Free'}
                            </span>
                          </td>
                        </tr>
                      )) : (
                        <tr>
                          <td colSpan="4" className="px-4 py-8 text-center text-gray-500 text-sm">No registered users collected yet.</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </section>
        )}
      </div>
    </div>
  );
}
