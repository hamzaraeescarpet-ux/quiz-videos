import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, Play, Square, Download, Trash2, Plus, Image as ImageIcon, FileText, MessageSquare, FileSpreadsheet, Zap, DollarSign, Sparkles, ArrowDown } from 'lucide-react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';

export default function Dashboard() {
  const { currentUser, login, credits, isPremium, consumeCredits } = useAuth();
  const navigate = useNavigate();

  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [rows, setRows] = useState([{ id: 1, question: '', option1: '', option2: '', option3: '', option4: '', answer: '' }]);
  const [logoFile, setLogoFile] = useState(null);
  
  // Custom Box Color state
  const [boxColor, setBoxColor] = useState('#E74C3C');
  // Custom Background Videos list state
  const [customBgFiles, setCustomBgFiles] = useState([]);
  // Quota full modal state
  const [showQuotaModal, setShowQuotaModal] = useState(false);
  // FAQ accordion state
  const [activeFaq, setActiveFaq] = useState(null);
  
  const [sessionId, setSessionId] = useState(() => localStorage.getItem('current_session_id') || null);
  const [status, setStatus] = useState(null); // 'Processing', 'Completed', 'Interrupted', 'Failed'
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [displayPercent, setDisplayPercent] = useState(0);
  const [isStopping, setIsStopping] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [showGenerateGuide, setShowGenerateGuide] = useState(false);
  const [generatedVideos, setGeneratedVideos] = useState([]);
  const generateSectionRef = useRef(null);
  const [pendingComplete, setPendingComplete] = useState(false);
  const startTimeRef = useRef(null);

  const demoRows = [
    { id: 'demo-population', question: 'Which country has the largest population?', option1: 'India', option2: 'China', option3: 'United States', option4: 'Indonesia', answer: 'India' },
    { id: 'demo-capital', question: 'What is the capital of the USA?', option1: 'New York City', option2: 'Washington, D.C.', option3: 'Los Angeles', option4: 'Chicago', answer: 'Washington, D.C.' }
  ];

  // Track time elapsed during rendering to show news ticker after 2 minutes (120s)
  useEffect(() => {
    if (status !== 'Processing') {
      setElapsedSeconds(0);
      return;
    }

    let initialSeconds = 0;
    try {
      if (sessionId) {
        const localHistory = JSON.parse(localStorage.getItem('quizviral_jobs_history') || '[]');
        const currentJob = localHistory.find(j => j.session_id === sessionId);
        if (currentJob && currentJob.created_at) {
          const startedAt = new Date(currentJob.created_at).getTime();
          initialSeconds = Math.max(0, Math.floor((Date.now() - startedAt) / 1000));
        }
      }
    } catch (e) {
      console.error(e);
    }
    setElapsedSeconds(initialSeconds);

    const timer = setInterval(() => {
      setElapsedSeconds(prev => prev + 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [status, sessionId]);

  useEffect(() => {
    if (pendingComplete && elapsedSeconds >= 120) {
      setStatus('Completed');
      setPendingComplete(false);
      localStorage.removeItem('current_session_id');
      setIsStopping(false);
    }
  }, [pendingComplete, elapsedSeconds]);

  useEffect(() => {
    // If we mount and already have a session, we assume it might be processing
    if (sessionId && !status) {
      setStatus('Processing');
    }
    
    axios.get('/api/hf/categories').then(res => {
      let cats = res.data.categories || [];
      // Always append "Custom Uploads 🎥" template category at the end
      if (!cats.includes('Custom Uploads 🎥')) {
        cats = [...cats, 'Custom Uploads 🎥'];
      }
      setCategories(cats);
      if (cats.length > 0) {
        setSelectedCategory(cats[0]);
      }
    }).catch(err => console.error("Error fetching categories", err));
  }, []);

  useEffect(() => {
    if (!sessionId || !['Completed', 'Interrupted'].includes(status)) {
      return;
    }

    axios.get(`/api/hf/videos/${sessionId}`).then(res => {
      setGeneratedVideos(res.data.videos || []);
    }).catch(err => {
      console.error("Failed to load generated video previews", err);
      setGeneratedVideos([]);
    });
  }, [sessionId, status]);

  useEffect(() => {
    let interval;
    let fakeProgressInterval;

    if (sessionId && status === 'Processing') {
      if (!startTimeRef.current) {
        let startedAtTime = Date.now();
        try {
          const localHistory = JSON.parse(localStorage.getItem('quizviral_jobs_history') || '[]');
          const currentJob = localHistory.find(j => j.session_id === sessionId);
          if (currentJob && currentJob.created_at) {
            startedAtTime = new Date(currentJob.created_at).getTime();
          }
        } catch (e) {
          console.error(e);
        }
        startTimeRef.current = startedAtTime;
      }

      // Poll real status every 2 seconds
      interval = setInterval(() => {
        axios.get(`/api/hf/status/${sessionId}`).then(res => {
          const backendStatus = res.data.status;
          const currentElapsed = Math.floor((Date.now() - (startTimeRef.current || Date.now())) / 1000);
          
          if (backendStatus === 'Completed') {
            setProgress({ current: res.data.completed_so_far, total: res.data.total_expected });
            if (currentElapsed >= 120) {
              setStatus('Completed');
              localStorage.removeItem('current_session_id');
              setIsStopping(false);
            } else {
              setPendingComplete(true);
            }
          } else {
            setStatus(backendStatus);
            setProgress({ current: res.data.completed_so_far, total: res.data.total_expected });
            if (['Failed', 'Interrupted'].includes(backendStatus)) {
              localStorage.removeItem('current_session_id');
              setIsStopping(false);
            }
          }
          
          // Update local history status
          try {
            const localHistory = JSON.parse(localStorage.getItem('quizviral_jobs_history') || '[]');
            const updated = localHistory.map(job => {
              if (job.session_id === sessionId) {
                return {
                  ...job,
                  status: backendStatus,
                  completed_so_far: res.data.completed_so_far,
                  total_expected: res.data.total_expected
                };
              }
              return job;
            });
            localStorage.setItem('quizviral_jobs_history', JSON.stringify(updated));
          } catch (e) {
            console.error("Failed to update local history status", e);
          }
        }).catch(err => {
          console.error(err);
          // If the backend lost the session (e.g. server restarted), clear it locally
          if (err.response && err.response.status === 404) {
             setStatus('Failed');
             localStorage.removeItem('current_session_id');
             
             // Update local history as Failed
             try {
               const localHistory = JSON.parse(localStorage.getItem('quizviral_jobs_history') || '[]');
               const updated = localHistory.map(job => {
                 if (job.session_id === sessionId) {
                   return { ...job, status: 'Failed' };
                 }
                 return job;
               });
               localStorage.setItem('quizviral_jobs_history', JSON.stringify(updated));
             } catch (e) {
               console.error(e);
             }
          }
        });
      }, 2000);

      // Smooth percentage animator
      fakeProgressInterval = setInterval(() => {
        setDisplayPercent((prev) => {
          if (progress.total === 0) return 0;
          
          const basePercent = Math.round((progress.current / progress.total) * 100);
          const chunkSize = Math.round((1 / progress.total) * 100);
          const cap = basePercent + chunkSize - 1; // e.g. cap at 19% if base is 0% and chunk is 20%

          // If we are completed, snap to 100
          if (progress.current === progress.total) {
            return status === 'Processing' ? 99 : 100;
          }
          
          // Slowly increment towards the cap
          if (prev < basePercent) return basePercent; // Catch up if behind
          if (prev < cap) return prev + 1; // Increment slowly
          return prev; // Stay at cap until real progress updates
        });
      }, 1500); // Increment 1% every 1.5 seconds (gives a smooth continuous feel)
    }
    
    if (status === 'Completed') {
      setDisplayPercent(100);
    }

    return () => {
      clearInterval(interval);
      clearInterval(fakeProgressInterval);
    };
  }, [sessionId, status, progress.current, progress.total, pendingComplete]);

  const onLogoDrop = useCallback(acceptedFiles => {
    setLogoFile(acceptedFiles[0]);
  }, []);

  const { getRootProps: getLogoProps, getInputProps: getLogoInputProps } = useDropzone({ 
    onDrop: onLogoDrop, 
    accept: {'image/*': ['.jpeg', '.jpg', '.png']} 
  });

  const handleRowChange = (index, field, value) => {
    const newRows = [...rows];
    newRows[index][field] = value;
    setRows(newRows);
  };

  const addRow = () => {
    if (rows.length < 150) {
      setRows([...rows, { id: Date.now(), question: '', option1: '', option2: '', option3: '', option4: '', answer: '' }]);
    }
  };

  const fillDemoData = () => {
    const builtInCategory = categories.find(category => !category.toLowerCase().includes('custom'));
    if (selectedCategory.toLowerCase().includes('custom') || !selectedCategory) {
      setSelectedCategory(builtInCategory || 'Mix');
      setCustomBgFiles([]);
    }
    setRows(demoRows);
    setShowGenerateGuide(true);
    window.setTimeout(() => {
      generateSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 150);
  };

  const removeRow = (index) => {
    if (rows.length > 1) {
      const newRows = [...rows];
      newRows.splice(index, 1);
      setRows(newRows);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.name.toLowerCase().endsWith('.csv')) {
      const reader = new FileReader();
      reader.onload = (evt) => {
        const text = evt.target.result;
        const lines = text.split('\n');
        const parsedRows = [];
        for (let i = 1; i < lines.length; i++) {
          const cols = lines[i].split(',').map(c => c.trim());
          if (cols.length >= 6) {
            parsedRows.push({
              id: Date.now() + i,
              question: cols[0],
              option1: cols[1],
              option2: cols[2],
              option3: cols[3],
              option4: cols[4],
              answer: cols[5],
            });
          }
        }
        if (parsedRows.length > 0) setRows(parsedRows.slice(0, 150));
      };
      reader.readAsText(file);
    }
  };

  const startGeneration = async () => {
    if (!currentUser) return login();

    const isValid = rows.every(r => r.question && r.option1 && r.option2 && r.option3 && r.option4 && r.answer);
    if (!isValid) return alert("Please fill all fields in the rows.");
    
    // Check custom background videos uploaded if they chose custom background category
    if (selectedCategory === 'Custom Uploads 🎥' && customBgFiles.length === 0) {
      return alert("Please upload at least one background video for Custom Uploads.");
    }

    // Verify credits - applies to both premium (100) and free (5) users
    if (rows.length > credits) {
      setShowQuotaModal(true);
      return;
    }

    if (!consumeCredits(rows.length)) {
       setShowQuotaModal(true);
       return;
    }

    const formData = new FormData();
    formData.append('questions', JSON.stringify(rows));
    formData.append('category', selectedCategory);
    formData.append('email', currentUser.email); // Send email for automation
    formData.append('box_color', boxColor); // Send the selected color
    
    if (logoFile) {
      formData.append('logo', logoFile);
    }

    // Append custom background videos if uploaded
    if (selectedCategory === 'Custom Uploads 🎥' && customBgFiles && customBgFiles.length > 0) {
      customBgFiles.forEach(file => {
        formData.append('custom_bg_videos', file);
      });
    }

    try {
      startTimeRef.current = Date.now();
      setPendingComplete(false);
      setShowGenerateGuide(false);
      setGeneratedVideos([]);
      setStatus('Processing');
      setProgress({ current: 0, total: rows.length });
      setDisplayPercent(0);
      
      const res = await axios.post('/api/hf/generate-bulk', formData);
      const newSessionId = res.data.session_id;
      setSessionId(newSessionId);
      localStorage.setItem('current_session_id', newSessionId);
      
      // Save to local history to survive backend restarts
      try {
        const localHistory = JSON.parse(localStorage.getItem('quizviral_jobs_history') || '[]');
        const newJob = {
          session_id: newSessionId,
          status: 'Processing',
          completed_so_far: 0,
          total_expected: rows.length,
          user_email: currentUser.email,
          created_at: new Date().toISOString()
        };
        localStorage.setItem('quizviral_jobs_history', JSON.stringify([newJob, ...localHistory]));
      } catch (e) {
        console.error("Failed to save job to local history", e);
      }
    } catch (err) {
      console.error(err);
      alert("Failed to start generation.");
      setStatus(null);
    }
  };

  const stopGeneration = async () => {
    if (sessionId) {
      try {
        setIsStopping(true);
        await axios.post(`/api/hf/stop-generation/${sessionId}`);
        
        // Update local history status to Interrupted
        try {
          const localHistory = JSON.parse(localStorage.getItem('quizviral_jobs_history') || '[]');
          const updated = localHistory.map(job => {
            if (job.session_id === sessionId) {
              return { ...job, status: 'Interrupted' };
            }
            return job;
          });
          localStorage.setItem('quizviral_jobs_history', JSON.stringify(updated));
        } catch (e) {
          console.error(e);
        }
      } catch (err) {
        console.error(err);
        alert("Failed to stop generation.");
        setIsStopping(false);
      }
    }
  };

  const downloadZip = () => {
    window.location.href = `/api/hf/download/${sessionId}`;
  };

  const resetState = () => {
    setStatus(null);
    setSessionId(null);
    setProgress({ current: 0, total: 0 });
    setDisplayPercent(0);
    setIsStopping(false);
    setElapsedSeconds(0);
    setShowGenerateGuide(false);
    setGeneratedVideos([]);
    setRows([{ id: Date.now(), question: '', option1: '', option2: '', option3: '', option4: '', answer: '' }]);
    localStorage.removeItem('current_session_id');
    startTimeRef.current = null;
    setPendingComplete(false);
  };

  // Helper to check if status is complete/failed and clear storage
  useEffect(() => {
    if (status === 'Completed' || status === 'Failed' || status === 'Interrupted') {
      localStorage.removeItem('current_session_id');
    }
  }, [status]);

  const [isCategoryDropdownOpen, setIsCategoryDropdownOpen] = useState(false);

  // Helper for category icons
  const getCategoryIcon = (cat) => {
    const lower = cat.toLowerCase();
    if (lower.includes('minecraft')) return '⛏️';
    if (lower.includes('nature')) return '🌲';
    if (lower.includes('space')) return '🚀';
    if (lower.includes('gta') || lower.includes('car')) return '🚗';
    if (lower.includes('subway')) return '🏃';
    if (lower.includes('asmr')) return '🔪';
    if (lower.includes('custom')) return '🎥';
    if (lower.includes('mix')) return '🔀';
    return '✨';
  };

  return (
    <div className="space-y-6 md:space-y-8 animate-in fade-in duration-500">
      <header className="px-2 border-b border-dark-700/60 pb-4 md:pb-6">
        <h1 className="text-2xl md:text-3xl font-extrabold mb-2">Create Viral Videos</h1>
        <p className="text-gray-400 text-sm md:text-base">Transform text into highly engaging trivia short videos instantly.</p>
      </header>

      {/* Step 1: Category Dropdown & Custom Videos area */}
      <section className="bg-white dark:bg-dark-800 p-4 md:p-6 rounded-xl border border-gray-200 dark:border-dark-700 shadow-xl relative z-20">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-3">
          <h2 className="text-lg md:text-xl font-semibold text-brand-300">1. Choose Template Category</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
          <div className="relative w-full">
            <button
              onClick={() => setIsCategoryDropdownOpen(!isCategoryDropdownOpen)}
              className="w-full bg-white dark:bg-dark-900 border border-gray-300 dark:border-dark-600 hover:border-brand-500 text-gray-800 dark:text-white px-4 py-3 rounded-lg flex items-center justify-between transition-all shadow-sm"
            >
              <div className="flex items-center gap-3">
                <span className="text-xl">{getCategoryIcon(selectedCategory)}</span>
                <span className="font-semibold">{selectedCategory || "Select Category"}</span>
              </div>
              <svg className={`w-5 h-5 transition-transform duration-200 ${isCategoryDropdownOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
            </button>

            {isCategoryDropdownOpen && (
              <div className="absolute top-full left-0 mt-2 w-full bg-white dark:bg-dark-800 border border-gray-200 dark:border-dark-600 rounded-lg shadow-2xl overflow-hidden z-50">
                {categories.length > 0 ? categories.map(cat => (
                  <button
                    key={cat}
                    onClick={() => {
                      setSelectedCategory(cat);
                      setIsCategoryDropdownOpen(false);
                    }}
                    className={`w-full text-left px-4 py-3 flex items-center gap-3 hover:bg-gray-100 dark:hover:bg-dark-700 text-gray-700 dark:text-gray-200 transition-colors ${selectedCategory === cat ? 'bg-brand-100 dark:bg-brand-900/30 border-l-2 border-brand-500' : ''}`}
                  >
                    <span className="text-xl">{getCategoryIcon(cat)}</span>
                    <span className="font-semibold">{cat}</span>
                  </button>
                )) : (
                  <div className="px-4 py-3 text-gray-500 text-sm">No categories found.</div>
                )}
              </div>
            )}
          </div>

          {/* Conditional Rendering of Custom Background Video Upload right inside Step 1 */}
          {selectedCategory === 'Custom Uploads 🎥' && (
            <motion.div 
              initial={{ opacity: 0, y: -10 }} 
              animate={{ opacity: 1, y: 0 }} 
              className="w-full"
            >
              <label className="border-2 border-dashed border-brand-500/40 rounded-xl p-4 text-center cursor-pointer hover:border-brand-500 transition-all bg-dark-900/70 flex flex-col items-center justify-center h-[110px] w-full shadow-lg shadow-brand-500/5">
                <input 
                  type="file" 
                  accept="video/*" 
                  multiple 
                  className="hidden" 
                  onChange={(e) => {
                    const files = Array.from(e.target.files);
                    setCustomBgFiles(files);
                  }} 
                />
                <UploadCloud className="h-7 w-7 text-brand-400 mb-2 animate-bounce" />
                {customBgFiles.length > 0 ? (
                  <p className="text-brand-300 font-bold text-xs break-all">
                    ✓ {customBgFiles.length} custom video(s) uploaded successfully!
                  </p>
                ) : (
                  <p className="text-gray-300 text-xs font-semibold">
                    Upload Custom Background Video(s)
                  </p>
                )}
                <span className="text-[10px] text-gray-500 mt-1">Supports multiple custom MP4s</span>
              </label>
            </motion.div>
          )}
        </div>
      </section>

      {/* Step 2: Data & Media */}
      <section className="bg-white dark:bg-dark-800 p-4 md:p-6 rounded-xl border border-gray-200 dark:border-dark-700 shadow-xl space-y-6 md:space-y-8 relative z-10">
        <h2 className="text-lg md:text-xl font-semibold text-brand-300">2. Input Data & Branding</h2>
        
        {/* Branding & Visual Customizations */}
        <div className="w-full">
          {/* Custom Logo */}
          <div className="w-full">
            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Upload Custom Logo (Optional)</label>
            <div 
              {...getLogoProps()} 
              className="border-2 border-dashed border-gray-300 dark:border-dark-600 rounded-xl p-4 text-center cursor-pointer hover:border-brand-500 transition-colors bg-gray-50 dark:bg-dark-900/50 flex flex-col items-center justify-center h-[120px]"
            >
              <input {...getLogoInputProps()} />
              <ImageIcon className="mx-auto h-6 w-6 text-gray-400 mb-2" />
              {logoFile ? (
                <p className="text-brand-600 dark:text-brand-400 font-bold text-xs break-all">Selected: {logoFile.name}</p>
              ) : (
                <p className="text-gray-400 text-xs font-medium">Tap or drag a custom logo here</p>
              )}
            </div>
          </div>
        </div>

        {/* Data Table */}
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <h3 className="font-medium text-gray-700 dark:text-gray-200">Questions Data</h3>
            <div className="flex w-full sm:w-auto flex-wrap items-center gap-3">
              <button
                onClick={fillDemoData}
                className="w-full sm:w-auto bg-gradient-to-r from-amber-400 to-orange-500 hover:from-amber-300 hover:to-orange-400 text-slate-950 px-4 py-2 md:py-1.5 rounded-md text-sm font-extrabold transition-all flex items-center justify-center gap-2 shadow-lg shadow-orange-500/25 hover:scale-[1.03] active:scale-95 cursor-pointer"
              >
                ✨ Try Demo / Test Data
              </button>
              <label className="flex-1 sm:flex-none cursor-pointer bg-gray-100 hover:bg-gray-200 dark:bg-dark-700 dark:hover:bg-dark-600 text-gray-700 dark:text-white px-3 py-2 md:py-1.5 rounded-md text-sm md:text-sm transition-colors border border-gray-200 dark:border-dark-600 flex items-center justify-center gap-2">
                <FileText className="w-4 h-4" />
                Upload CSV
                <input type="file" accept=".csv, text/csv" className="hidden" onChange={handleFileUpload} />
              </label>
              <button onClick={addRow} className="flex-1 sm:flex-none bg-brand-600 hover:bg-brand-500 text-white px-3 py-2 md:py-1.5 rounded-md text-sm md:text-sm transition-colors flex items-center justify-center gap-2 shadow-lg shadow-brand-500/20">
                <Plus className="w-4 h-4" /> Add Row
              </button>
            </div>
          </div>
          
          <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-dark-600 shadow-sm w-full touch-pan-x">
            <table className="w-full text-sm text-left min-w-[800px]">
              <thead className="text-xs text-gray-600 dark:text-gray-300 uppercase bg-gray-100 dark:bg-dark-900">
                <tr>
                  <th className="px-3 py-3 w-[20%]">Question</th>
                  <th className="px-3 py-3 w-[14%]">Opt A</th>
                  <th className="px-3 py-3 w-[14%]">Opt B</th>
                  <th className="px-3 py-3 w-[14%]">Opt C</th>
                  <th className="px-3 py-3 w-[14%]">Opt D</th>
                  <th className="px-3 py-3 w-[18%]">Answer</th>
                  <th className="px-3 py-3 w-[6%] text-center">Act</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row, idx) => (
                  <tr key={row.id} className="bg-white dark:bg-dark-800 border-b border-gray-200 dark:border-dark-700 hover:bg-gray-50 dark:hover:bg-dark-700/50">
                    <td className="p-2"><input className="w-full bg-white dark:bg-dark-900 border border-gray-300 dark:border-dark-600 rounded px-2 py-2 md:py-1.5 focus:ring-2 focus:ring-brand-500 outline-none text-sm placeholder-gray-400 dark:placeholder-gray-500 text-gray-800 dark:text-gray-100" placeholder="Question..." value={row.question} onChange={e => handleRowChange(idx, 'question', e.target.value)} /></td>
                    <td className="p-2"><input className="w-full bg-white dark:bg-dark-900 border border-gray-300 dark:border-dark-600 rounded px-2 py-2 md:py-1.5 focus:ring-2 focus:ring-brand-500 outline-none text-sm placeholder-gray-400 dark:placeholder-gray-500 text-gray-800 dark:text-gray-100" placeholder="Option A" value={row.option1} onChange={e => handleRowChange(idx, 'option1', e.target.value)} /></td>
                    <td className="p-2"><input className="w-full bg-white dark:bg-dark-900 border border-gray-300 dark:border-dark-600 rounded px-2 py-2 md:py-1.5 focus:ring-2 focus:ring-brand-500 outline-none text-sm placeholder-gray-400 dark:placeholder-gray-500 text-gray-800 dark:text-gray-100" placeholder="Option B" value={row.option2} onChange={e => handleRowChange(idx, 'option2', e.target.value)} /></td>
                    <td className="p-2"><input className="w-full bg-white dark:bg-dark-900 border border-gray-300 dark:border-dark-600 rounded px-2 py-2 md:py-1.5 focus:ring-2 focus:ring-brand-500 outline-none text-sm placeholder-gray-400 dark:placeholder-gray-500 text-gray-800 dark:text-gray-100" placeholder="Option C" value={row.option3} onChange={e => handleRowChange(idx, 'option3', e.target.value)} /></td>
                    <td className="p-2"><input className="w-full bg-white dark:bg-dark-900 border border-gray-300 dark:border-dark-600 rounded px-2 py-2 md:py-1.5 focus:ring-2 focus:ring-brand-500 outline-none text-sm placeholder-gray-400 dark:placeholder-gray-500 text-gray-800 dark:text-gray-100" placeholder="Option D" value={row.option4} onChange={e => handleRowChange(idx, 'option4', e.target.value)} /></td>
                    <td className="p-2"><input className="w-full bg-white dark:bg-dark-900 border border-gray-300 dark:border-dark-600 rounded px-2 py-2 md:py-1.5 focus:ring-2 focus:ring-brand-500 outline-none text-sm placeholder-gray-400 dark:placeholder-gray-500 text-gray-800 dark:text-gray-100" placeholder="Correct Answer" value={row.answer} onChange={e => handleRowChange(idx, 'answer', e.target.value)} /></td>
                    <td className="p-2 text-center">
                      <button onClick={() => removeRow(idx)} className="text-red-400 hover:text-red-300 transition-colors p-2 rounded-full hover:bg-red-500/10">
                        <Trash2 className="w-4 h-4 mx-auto" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Step 3: Generation Control */}
      <section ref={generateSectionRef} className="bg-dark-800 p-4 md:p-6 rounded-xl border border-dark-700 shadow-xl flex flex-col items-center relative">
        {!status ? (
          <>
            {showGenerateGuide && (
              <motion.div
                initial={{ opacity: 0, y: -12, scale: 0.96 }}
                animate={{ opacity: 1, y: [0, 6, 0], scale: 1 }}
                transition={{ opacity: { duration: 0.25 }, scale: { duration: 0.25 }, y: { duration: 1.25, repeat: Infinity } }}
                className="mb-4 max-w-md rounded-xl border border-amber-400/60 bg-amber-400 px-4 py-3 text-center text-sm font-extrabold text-slate-950 shadow-xl shadow-amber-500/25"
              >
                Awesome! Now click here to generate your videos in 1-click 🚀
                <ArrowDown className="mx-auto mt-1 h-6 w-6" />
              </motion.div>
            )}
            <button
              onClick={startGeneration}
              className={`w-full md:max-w-md py-4 px-4 rounded-xl bg-gradient-to-r from-brand-600 to-brand-400 text-white font-bold text-base md:text-lg hover:from-brand-500 hover:to-brand-300 transition-all shadow-lg shadow-brand-500/25 flex items-center justify-center gap-2 transform hover:scale-105 active:scale-95 ${showGenerateGuide ? 'ring-4 ring-amber-400/70 ring-offset-4 ring-offset-dark-800' : ''}`}
            >
              <Play className="fill-current w-5 h-5" />
              {!currentUser
                ? 'Generate Bulk Videos'
                : isPremium
                  ? 'Generate Bulk Videos'
                  : `Generate Bulk Videos (${credits} Credits Left)`
              }
            </button>
          </>
        ) : (
          <div className="w-full space-y-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <h3 className="text-base md:text-lg font-bold text-brand-300">
                  {status === 'Processing' ? 'Rendering in progress...' : status === 'Completed' ? 'Generation Complete!' : 'Generation Interrupted'}
                </h3>
                <p className="text-gray-400 text-sm">
                  {progress.current} of {progress.total} videos completed ({displayPercent}%)
                </p>
                {status === 'Processing' && (
                  <p className="text-brand-400 text-xs mt-2 italic">
                    Your bulk generation is rendering. Just minimize this tab and come back after some time; your bulk videos will be generated.
                  </p>
                )}
              </div>
              {status === 'Processing' && (
                <button 
                  onClick={stopGeneration}
                  disabled={isStopping}
                  className={`w-full sm:w-auto px-4 py-2 rounded-lg font-semibold transition-all flex items-center justify-center gap-2 text-sm ${
                    isStopping 
                      ? 'bg-yellow-500/10 text-yellow-500 border border-yellow-500/50 cursor-not-allowed'
                      : 'bg-red-500/10 text-red-500 border border-red-500/50 hover:bg-red-500 hover:text-white'
                  }`}
                >
                  {isStopping ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-yellow-500 border-t-transparent" />
                      Stopping (Saving ZIP)...
                    </>
                  ) : (
                    <>
                      <Square className="fill-current w-4 h-4" />
                      Stop & Download
                    </>
                  )}
                </button>
              )}
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-dark-900 rounded-full h-3 md:h-4 overflow-hidden shadow-inner relative">
              <motion.div 
                className="bg-gradient-to-r from-brand-500 to-blue-500 h-3 md:h-4"
                initial={{ width: 0 }}
                animate={{ width: `${displayPercent}%` }}
                transition={{ duration: 0.5, ease: "linear" }}
              />
              <span className="absolute inset-0 flex items-center justify-center text-[10px] md:text-xs font-bold text-white drop-shadow-md mix-blend-difference">
                {displayPercent}%
              </span>
            </div>

            {status === 'Processing' && elapsedSeconds >= 120 && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="w-full overflow-hidden bg-gradient-to-r from-amber-500/10 via-orange-500/10 to-amber-500/10 border border-amber-400/30 rounded-xl py-3 px-4 shadow-xl relative"
              >
                <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                  <div className="flex items-center gap-3 w-full overflow-hidden">
                    <span className="flex h-3 w-3 relative shrink-0">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-3 w-3 bg-amber-500"></span>
                    </span>
                    <div className="ticker-wrap w-full overflow-hidden text-left">
                      <style dangerouslySetInnerHTML={{__html: `
                        @keyframes premium-marquee {
                          0% { transform: translate3d(0%, 0, 0); }
                          100% { transform: translate3d(-50%, 0, 0); }
                        }
                        .premium-ticker-move {
                          display: inline-block;
                          white-space: nowrap;
                          animation: premium-marquee 25s linear infinite;
                        }
                      `}} />
                      <div className="premium-ticker-move text-sm font-extrabold text-amber-300">
                        Loved the speed? Unlock Unlimited High-Speed Renderings, Premium AI Voices &amp; 500+ backgrounds! &nbsp;&nbsp;&nbsp;&nbsp; ★ &nbsp;&nbsp;&nbsp;&nbsp; Loved the speed? Unlock Unlimited High-Speed Renderings, Premium AI Voices &amp; 500+ backgrounds! &nbsp;&nbsp;&nbsp;&nbsp; ★ &nbsp;&nbsp;&nbsp;&nbsp;
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => navigate('/pricing')}
                    className="shrink-0 bg-gradient-to-r from-amber-400 to-orange-500 hover:from-amber-300 hover:to-orange-400 text-slate-950 font-black text-xs md:text-sm px-4 py-2 rounded-lg transition-all shadow-md shadow-orange-500/30 hover:scale-105 active:scale-95 cursor-pointer"
                  >
                    Upgrade to Premium Now
                  </button>
                </div>
              </motion.div>
            )}

            {/* Legacy rendering-help ticker is intentionally hidden in favor of the premium banner above. */}
            {status === 'Processing' && elapsedSeconds < 0 && (
              <div className="w-full overflow-hidden bg-brand-500/5 border border-brand-500/20 rounded-lg py-2 mt-2 relative">
                <style dangerouslySetInnerHTML={{__html: `
                  @keyframes ticker-marquee {
                    0% { transform: translate3d(0%, 0, 0); }
                    100% { transform: translate3d(-100%, 0, 0); }
                  }
                  .ticker-wrap {
                    overflow: hidden;
                    width: 100%;
                    white-space: nowrap;
                  }
                  .ticker-move {
                    display: inline-block;
                    padding-left: 100%;
                    animation: ticker-marquee 35s linear infinite;
                    will-change: transform;
                  }
                `}} />
                <div className="ticker-wrap">
                  <div className="ticker-move text-xs md:text-sm font-semibold text-brand-300">
                    💡 If you feel the rendering is taking too long, feel free to stop it. You will get a ZIP file containing all the videos finished so far, and you can generate the remaining ones later or you Just minimize this tab and come back after some time; your bulk videos will be generated.
                  </div>
                </div>
              </div>
            )}

            {(status === 'Completed' || status === 'Interrupted') && (
              <div className="space-y-6 pt-2 md:pt-4">
                {generatedVideos.length > 0 && (
                  <div>
                    <h4 className="mb-4 text-center text-lg font-extrabold text-brand-300">Your Generated Video Previews</h4>
                    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
                      {generatedVideos.map((video, index) => (
                        <div key={video.filename} className="overflow-hidden rounded-xl border border-dark-600 bg-dark-900 shadow-xl">
                          <video controls preload="metadata" className="aspect-[9/16] w-full bg-black" src={`/api/hf/videos/${sessionId}/${encodeURIComponent(video.filename)}`} />
                          <p className="px-3 py-2 text-center text-xs font-bold text-gray-300">Video {index + 1}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                <div className="flex flex-col sm:flex-row justify-center gap-4">
                  <button
                    onClick={downloadZip}
                    className="w-full sm:w-auto bg-green-600 hover:bg-green-500 text-white px-6 md:px-8 py-3 rounded-xl font-bold text-base md:text-lg transition-all shadow-lg shadow-green-600/20 flex items-center justify-center gap-2"
                  >
                    <Download className="w-5 h-5" />
                    Download ZIP
                  </button>
                  <button
                    onClick={resetState}
                    className="w-full sm:w-auto bg-dark-700 hover:bg-dark-600 text-white px-6 md:px-8 py-3 rounded-xl font-bold text-base md:text-lg transition-all flex items-center justify-center gap-2"
                  >
                    <Plus className="w-5 h-5" />
                    Start New Bulk
                  </button>
                </div>
              </div>
            )}
            {status === 'Failed' && (
              <div className="mt-4 p-4 bg-red-900/50 border border-red-500/50 rounded-lg text-white">
                <h3 className="font-bold text-red-400 mb-2">Generation Failed! (Server may have restarted)</h3>
                <p className="text-sm">Please visit <a href="/api/hf/logs" target="_blank" className="underline text-blue-300">this link</a> to see the exact error.</p>
                <button onClick={resetState} className="mt-3 px-4 py-2 bg-dark-700 hover:bg-dark-600 rounded text-sm font-semibold">Start New Bulk</button>
              </div>
            )}
          </div>
        )}
      </section>

      {/* How To Launch Your Viral Channel Section */}
      {/* Step 3: How it Works Section */}
      <section className="bg-white dark:bg-dark-800 p-6 md:p-8 rounded-xl border border-gray-200 dark:border-dark-700 shadow-xl space-y-8 mt-12">
        <div className="text-center space-y-2">
          <h2 className="text-2xl md:text-3xl font-extrabold text-gray-900 dark:text-white flex items-center justify-center gap-2">
            🔄 How To Launch Your Viral Channel in 4 Simple Steps
          </h2>
          <p className="text-gray-600 dark:text-gray-400 text-sm md:text-base max-w-2xl mx-auto">
            Our optimized ChatGPT-to-CSV workflow allows you to pump out high-retention short content at scale.
          </p>
        </div>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 pt-4">
          {/* Step 1 */}
          <div className="bg-dark-900/60 p-6 rounded-xl border border-dark-700/60 flex flex-col justify-between hover:border-brand-500/50 transition-all relative overflow-hidden group">
            <span className="absolute right-4 top-4 text-4xl font-extrabold text-dark-800 select-none group-hover:text-brand-500/10 transition-colors">01</span>
            <div className="space-y-3 z-10">
              <div className="w-10 h-10 rounded-lg bg-brand-500/10 border border-brand-500/25 flex items-center justify-center text-brand-400">
                <MessageSquare className="w-5 h-5" />
              </div>
              <span className="text-[10px] uppercase tracking-wider text-brand-400 font-bold">Step 1: 🤖 ChatGPT</span>
              <h3 className="text-sm font-bold text-gray-200">Pick Your Niche & Prompt</h3>
              <p className="text-xs text-gray-400 leading-relaxed">Go to ChatGPT, choose your favorite niche (like US Trivia, History, or Riddles), and ask it to generate unlimited quiz questions based on your topic.</p>
            </div>
          </div>
          
          {/* Step 2 */}
          <div className="bg-dark-900/60 p-6 rounded-xl border border-dark-700/60 flex flex-col justify-between hover:border-brand-500/50 transition-all relative overflow-hidden group">
            <span className="absolute right-4 top-4 text-4xl font-extrabold text-dark-800 select-none group-hover:text-brand-500/10 transition-colors">02</span>
            <div className="space-y-3 z-10">
              <div className="w-10 h-10 rounded-lg bg-brand-500/10 border border-brand-500/25 flex items-center justify-center text-brand-400">
                <FileSpreadsheet className="w-5 h-5" />
              </div>
              <span className="text-[10px] uppercase tracking-wider text-brand-400 font-bold">Step 2: 📊 Spreadsheets</span>
              <h3 className="text-sm font-bold text-gray-200">Create & Download CSV</h3>
              <p className="text-xs text-gray-400 leading-relaxed">Organize those ChatGPT responses into a simple spreadsheet and download it as a .csv file. No manual typing or complex formatting needed.</p>
            </div>
          </div>
          
          {/* Step 3 */}
          <div className="bg-dark-900/60 p-6 rounded-xl border border-dark-700/60 flex flex-col justify-between hover:border-brand-500/50 transition-all relative overflow-hidden group">
            <span className="absolute right-4 top-4 text-4xl font-extrabold text-dark-800 select-none group-hover:text-brand-500/10 transition-colors">03</span>
            <div className="space-y-3 z-10">
              <div className="w-10 h-10 rounded-lg bg-brand-500/10 border border-brand-500/25 flex items-center justify-center text-brand-400">
                <Zap className="w-5 h-5" />
              </div>
              <span className="text-[10px] uppercase tracking-wider text-brand-400 font-bold">Step 3: 🚀 Bulk Render</span>
              <h3 className="text-sm font-bold text-gray-200">1-Click Bulk Generation</h3>
              <p className="text-xs text-gray-400 leading-relaxed">Upload your CSV file to QuizViral AI. Our system instantly auto-injects premium narration, dynamic progress bars, and high-retention backgrounds to render bulk vertical videos at once.</p>
            </div>
          </div>
          
          {/* Step 4 */}
          <div className="bg-dark-900/60 p-6 rounded-xl border border-dark-700/60 flex flex-col justify-between hover:border-brand-500/50 transition-all relative overflow-hidden group">
            <span className="absolute right-4 top-4 text-4xl font-extrabold text-dark-800 select-none group-hover:text-brand-500/10 transition-colors">04</span>
            <div className="space-y-3 z-10">
              <div className="w-10 h-10 rounded-lg bg-brand-500/10 border border-brand-500/25 flex items-center justify-center text-brand-400">
                <DollarSign className="w-5 h-5" />
              </div>
              <span className="text-[10px] uppercase tracking-wider text-brand-400 font-bold">Step 4: 💰 Post & Earn</span>
              <h3 className="text-sm font-bold text-gray-200">Schedule, Dominate & Earn</h3>
              <p className="text-xs text-gray-400 leading-relaxed">Post these high-retention 9:16 videos on Facebook Reels, YouTube Shorts, and Instagram. Sit back and unlock massive passive income via the Facebook Performance Bonus and monetization programs!</p>
            </div>
          </div>
        </div>
      </section>

      {/* Frequently Asked Questions (FAQ) Accordion dropdown Section */}
      <section className="bg-white dark:bg-dark-800 p-6 md:p-8 rounded-xl border border-gray-200 dark:border-dark-700 shadow-xl space-y-6 mt-12">
        <div className="text-center space-y-2">
          <h2 className="text-2xl md:text-3xl font-extrabold text-gray-900 dark:text-white">Frequently Asked Questions 💬</h2>
          <p className="text-gray-600 dark:text-gray-400 text-sm md:text-base max-w-xl mx-auto">Get answers to the most common questions about monetization, daily limits, and more.</p>
        </div>
        
        <div className="space-y-3 max-w-3xl mx-auto pt-4">
          {[
            {
              q: "Can I monetize these videos on Facebook and YouTube?",
              ans: "Yes! QuizViral AI generates fully compliance-friendly videos optimized for the Facebook Performance Bonus program, Instagram Reels, and YouTube Shorts monetization."
            },
            {
              q: "What is the daily cap for video generation?",
              ans: "Premium members get access to a high daily video generation quota designed for massive scale and bulk workflows."
            },
            {
              q: "Is there a refund policy?",
              ans: "Due to the digital nature of bulk rendering and our free trial availability, we do not offer refunds once paid assets are generated. However, you can cancel your subscription instantly anytime to stop future renewals."
            },
            {
              q: "Do I need any editing experience?",
              ans: "Zero experience needed. Our automated dashboard handles scripts, visuals, and timing in 1-click."
            }
          ].map((item, idx) => (
            <div key={idx} className="bg-gray-50 dark:bg-dark-900 rounded-xl border border-gray-200 dark:border-dark-700/60 overflow-hidden transition-all">
              <button 
                onClick={() => setActiveFaq(activeFaq === idx ? null : idx)}
                className="w-full text-left px-5 py-4 flex items-center justify-between text-sm md:text-base font-bold text-gray-800 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-dark-800 transition-colors"
              >
                <span>{item.q}</span>
                <span className="text-brand-600 dark:text-brand-400 text-lg transition-transform duration-300 transform">
                  {activeFaq === idx ? '−' : '+'}
                </span>
              </button>
              
              {activeFaq === idx && (
                <div className="px-5 pb-5 pt-1 text-xs md:text-sm text-gray-600 dark:text-gray-400 border-t border-gray-200 dark:border-dark-800/80 leading-relaxed animate-in slide-in-from-top duration-300">
                  {item.ans}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Quota Exhausted Modal Alert */}
      {showQuotaModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/75 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-dark-800 border border-dark-700 p-6 md:p-8 rounded-2xl max-w-md w-[90%] text-center shadow-2xl space-y-6 animate-in zoom-in duration-300">
            <div className="w-16 h-16 bg-brand-500/10 text-brand-500 rounded-full flex items-center justify-center mx-auto border border-brand-500/20">
              <span className="text-3xl">⏰</span>
            </div>
            
            <div>
              <h3 className="text-xl font-extrabold text-white mb-2">Today's quota is full!</h3>
              {isPremium ? (
                <p className="text-gray-300 text-sm leading-relaxed">
                  Premium users are limited to **100 videos per day**. Please come back tomorrow to get another fresh 100 quota generation!
                </p>
              ) : (
                <p className="text-gray-300 text-sm leading-relaxed">
                  Please come back tomorrow to get **5 more free videos**, or subscribe to Premium right now for **100 videos daily**!
                </p>
              )}
            </div>
            
            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              {!isPremium && (
                <button
                  onClick={() => {
                    setShowQuotaModal(false);
                    navigate('/pricing');
                  }}
                  className="flex-1 py-3 px-4 rounded-xl bg-gradient-to-r from-brand-600 to-brand-400 text-white font-bold text-sm md:text-base hover:from-brand-500 hover:to-brand-300 transition-all shadow-lg shadow-brand-500/20"
                >
                  Subscribe to Premium
                </button>
              )}
              <button
                onClick={() => setShowQuotaModal(false)}
                className="w-full py-3 px-4 rounded-xl bg-dark-700 hover:bg-dark-600 text-white font-semibold text-sm md:text-base transition-all border border-dark-600"
              >
                Okay, I'll wait
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
