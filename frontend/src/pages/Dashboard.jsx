import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, Play, Square, Download, Trash2, Plus, Image as ImageIcon, FileText } from 'lucide-react';
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
    let interval;
    let fakeProgressInterval;

    if (sessionId && status === 'Processing') {
      // Poll real status every 2 seconds
      interval = setInterval(() => {
        axios.get(`/api/hf/status/${sessionId}`).then(res => {
          setStatus(res.data.status);
          setProgress({ current: res.data.completed_so_far, total: res.data.total_expected });
        }).catch(err => {
          console.error(err);
          // If the backend lost the session (e.g. server restarted), clear it locally
          if (err.response && err.response.status === 404) {
             setStatus('Failed');
             localStorage.removeItem('current_session_id');
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
          if (progress.current === progress.total) return 100;
          
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
  }, [sessionId, status, progress.current, progress.total]);

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
    if (rows.length < 100) {
      setRows([...rows, { id: Date.now(), question: '', option1: '', option2: '', option3: '', option4: '', answer: '' }]);
    }
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
        if (parsedRows.length > 0) setRows(parsedRows.slice(0, 100));
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
      setStatus('Processing');
      setProgress({ current: 0, total: rows.length });
      setDisplayPercent(0);
      
      const res = await axios.post('/api/hf/generate-bulk', formData);
      const newSessionId = res.data.session_id;
      setSessionId(newSessionId);
      localStorage.setItem('current_session_id', newSessionId);
    } catch (err) {
      console.error(err);
      alert("Failed to start generation.");
      setStatus(null);
    }
  };

  const stopGeneration = async () => {
    if (sessionId) {
      try {
        await axios.post(`/api/hf/stop-generation/${sessionId}`);
        setStatus('Interrupted');
        localStorage.removeItem('current_session_id');
      } catch (err) {
        console.error(err);
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
    setRows([{ id: Date.now(), question: '', option1: '', option2: '', option3: '', option4: '', answer: '' }]);
    localStorage.removeItem('current_session_id');
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
    if (lower.includes('satisfy')) return '🫧';
    if (lower.includes('nature')) return '🌲';
    if (lower.includes('space')) return '🚀';
    if (lower.includes('gta')) return '🚗';
    if (lower.includes('subway')) return '🏃';
    if (lower.includes('asmr')) return '🔪';
    if (lower.includes('custom')) return '🎥';
    return '✨';
  };

  return (
    <div className="space-y-6 md:space-y-8 animate-in fade-in duration-500">
      <header className="px-2">
        <h1 className="text-2xl md:text-3xl font-extrabold mb-2">Create Viral Videos</h1>
        <p className="text-gray-400 text-sm md:text-base">Transform text into highly engaging trivia short videos instantly.</p>
      </header>

      {/* Step 1: Category Dropdown & Custom Videos area */}
      <section className="bg-dark-800 p-4 md:p-6 rounded-xl border border-dark-700 shadow-xl relative z-20">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-3">
          <h2 className="text-lg md:text-xl font-semibold text-brand-300">1. Choose Template Category</h2>
          
          {/* Account Status Card to make daily quota limit visually clear */}
          {currentUser && (
            <div className="bg-dark-900 px-3 py-1.5 rounded-lg border border-dark-700 flex items-center gap-2 text-xs">
              <span className="text-gray-400 font-medium">Account Status:</span>
              <span className={`font-bold ${isPremium ? 'text-amber-400 flex items-center gap-1' : 'text-brand-400'}`}>
                {isPremium ? '👑 Premium' : '🌟 Free Plan'}
              </span>
              <span className="text-dark-500">|</span>
              <span className="text-gray-400">Daily Quota:</span>
              <span className="text-white font-mono font-bold bg-dark-800 px-1.5 py-0.5 rounded border border-dark-600">
                {credits} / {isPremium ? 100 : 5} Left
              </span>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
          <div className="relative w-full">
            <button
              onClick={() => setIsCategoryDropdownOpen(!isCategoryDropdownOpen)}
              className="w-full bg-dark-900 border border-dark-600 hover:border-brand-500 text-white px-4 py-3 rounded-lg flex items-center justify-between transition-all"
            >
              <div className="flex items-center gap-3">
                <span className="text-xl">{getCategoryIcon(selectedCategory)}</span>
                <span className="font-medium">{selectedCategory || "Select Category"}</span>
              </div>
              <svg className={`w-5 h-5 transition-transform duration-200 ${isCategoryDropdownOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
            </button>

            {isCategoryDropdownOpen && (
              <div className="absolute top-full left-0 mt-2 w-full bg-dark-800 border border-dark-600 rounded-lg shadow-2xl overflow-hidden z-50">
                {categories.length > 0 ? categories.map(cat => (
                  <button
                    key={cat}
                    onClick={() => {
                      setSelectedCategory(cat);
                      setIsCategoryDropdownOpen(false);
                    }}
                    className={`w-full text-left px-4 py-3 flex items-center gap-3 hover:bg-dark-700 transition-colors ${selectedCategory === cat ? 'bg-brand-900/30 border-l-2 border-brand-500' : ''}`}
                  >
                    <span className="text-xl">{getCategoryIcon(cat)}</span>
                    <span className="font-medium text-gray-200">{cat}</span>
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
      <section className="bg-dark-800 p-4 md:p-6 rounded-xl border border-dark-700 shadow-xl space-y-6 md:space-y-8 relative z-10">
        <h2 className="text-lg md:text-xl font-semibold text-brand-300">2. Input Data & Branding</h2>
        
        {/* Branding & Visual Customizations */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Custom Logo */}
          <div className="w-full">
            <label className="block text-sm font-semibold text-gray-300 mb-2">Upload Custom Logo (Optional)</label>
            <div 
              {...getLogoProps()} 
              className="border-2 border-dashed border-dark-600 rounded-xl p-4 text-center cursor-pointer hover:border-brand-500 transition-colors bg-dark-900/50 flex flex-col items-center justify-center h-[120px]"
            >
              <input {...getLogoInputProps()} />
              <ImageIcon className="mx-auto h-6 w-6 text-gray-400 mb-2" />
              {logoFile ? (
                <p className="text-brand-400 font-bold text-xs break-all">Selected: {logoFile.name}</p>
              ) : (
                <p className="text-gray-400 text-xs font-medium">Tap or drag a custom logo here</p>
              )}
            </div>
          </div>

          {/* Elegant Rainbow Color Picker Panel (Single Rainbow Button for Desktop & Mobile) */}
          <div className="bg-dark-900/60 p-4 rounded-xl border border-dark-700/80 shadow-md flex flex-col justify-center">
            <label className="block text-sm font-semibold text-gray-200 mb-3">Choose Video Text Box Theme Color</label>
            <div className="flex items-center gap-4">
              {/* Single multi-color rainbow circle button */}
              <div 
                className="relative w-14 h-14 rounded-full overflow-hidden border-2 border-white cursor-pointer shadow-lg hover:scale-110 active:scale-95 transition-all flex items-center justify-center"
                style={{ background: 'conic-gradient(from 0deg, red, yellow, green, cyan, blue, magenta, red)' }}
                title="Tap to select custom color"
              >
                <input
                  type="color"
                  value={boxColor}
                  onChange={(e) => setBoxColor(e.target.value)}
                  className="absolute inset-0 w-full h-full cursor-pointer opacity-0"
                />
                {/* Small inner dot showing currently selected color for feedback */}
                <div 
                  style={{ backgroundColor: boxColor }}
                  className="w-6 h-6 rounded-full border-2 border-white pointer-events-none shadow"
                />
              </div>
              
              <div className="flex flex-col gap-1">
                <span className="text-xs text-gray-400 font-semibold uppercase">Selected Theme Color</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-mono text-gray-200 font-bold bg-dark-800 px-3 py-1.5 rounded-lg border border-dark-600 uppercase tracking-wider">{boxColor}</span>
                  <div 
                    style={{ backgroundColor: boxColor }}
                    className="w-5 h-5 rounded border border-dark-600 shadow"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Data Table */}
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <h3 className="font-medium text-gray-200">Questions Data</h3>
            <div className="flex w-full sm:w-auto items-center gap-3">
              <label className="flex-1 sm:flex-none cursor-pointer bg-dark-700 hover:bg-dark-600 text-white px-3 py-2 md:py-1.5 rounded-md text-sm md:text-sm transition-colors flex items-center justify-center gap-2">
                <FileText className="w-4 h-4" />
                Upload CSV
                <input type="file" accept=".csv, text/csv" className="hidden" onChange={handleFileUpload} />
              </label>
              <button onClick={addRow} className="flex-1 sm:flex-none bg-brand-600 hover:bg-brand-500 text-white px-3 py-2 md:py-1.5 rounded-md text-sm md:text-sm transition-colors flex items-center justify-center gap-2 shadow-lg shadow-brand-500/20">
                <Plus className="w-4 h-4" /> Add Row
              </button>
            </div>
          </div>
          
          <div className="overflow-x-auto rounded-lg border border-dark-600 shadow-sm w-full touch-pan-x">
            <table className="w-full text-sm text-left min-w-[800px]">
              <thead className="text-xs text-gray-300 uppercase bg-dark-900">
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
                  <tr key={row.id} className="bg-dark-800 border-b border-dark-700 hover:bg-dark-700/50">
                    <td className="p-2"><input className="w-full bg-dark-900 border border-dark-600 rounded px-2 py-2 md:py-1.5 focus:ring-2 focus:ring-brand-500 outline-none text-sm placeholder-gray-500" placeholder="Question..." value={row.question} onChange={e => handleRowChange(idx, 'question', e.target.value)} /></td>
                    <td className="p-2"><input className="w-full bg-dark-900 border border-dark-600 rounded px-2 py-2 md:py-1.5 focus:ring-2 focus:ring-brand-500 outline-none text-sm placeholder-gray-500" placeholder="Option A" value={row.option1} onChange={e => handleRowChange(idx, 'option1', e.target.value)} /></td>
                    <td className="p-2"><input className="w-full bg-dark-900 border border-dark-600 rounded px-2 py-2 md:py-1.5 focus:ring-2 focus:ring-brand-500 outline-none text-sm placeholder-gray-500" placeholder="Option B" value={row.option2} onChange={e => handleRowChange(idx, 'option2', e.target.value)} /></td>
                    <td className="p-2"><input className="w-full bg-dark-900 border border-dark-600 rounded px-2 py-2 md:py-1.5 focus:ring-2 focus:ring-brand-500 outline-none text-sm placeholder-gray-500" placeholder="Option C" value={row.option3} onChange={e => handleRowChange(idx, 'option3', e.target.value)} /></td>
                    <td className="p-2"><input className="w-full bg-dark-900 border border-dark-600 rounded px-2 py-2 md:py-1.5 focus:ring-2 focus:ring-brand-500 outline-none text-sm placeholder-gray-500" placeholder="Option D" value={row.option4} onChange={e => handleRowChange(idx, 'option4', e.target.value)} /></td>
                    <td className="p-2"><input className="w-full bg-dark-900 border border-dark-600 rounded px-2 py-2 md:py-1.5 focus:ring-2 focus:ring-brand-500 outline-none text-sm placeholder-gray-500" placeholder="Correct Answer" value={row.answer} onChange={e => handleRowChange(idx, 'answer', e.target.value)} /></td>
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
      <section className="bg-dark-800 p-4 md:p-6 rounded-xl border border-dark-700 shadow-xl flex flex-col items-center">
        {!status ? (
          <button 
            onClick={startGeneration}
            className="w-full md:max-w-md py-4 px-4 rounded-xl bg-gradient-to-r from-brand-600 to-brand-400 text-white font-bold text-base md:text-lg hover:from-brand-500 hover:to-brand-300 transition-all shadow-lg shadow-brand-500/25 flex items-center justify-center gap-2 transform hover:scale-105 active:scale-95"
          >
            <Play className="fill-current w-5 h-5" />
            {isPremium ? `Generate Bulk Videos (${credits} Credits Left Today)` : `Generate Bulk Videos (${credits} Credits Left)`}
          </button>
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
                    Sit back and relax, your bulk videos are being generated. We will email you once they are ready to download!
                  </p>
                )}
              </div>
              {status === 'Processing' && (
                <button 
                  onClick={stopGeneration}
                  className="w-full sm:w-auto bg-red-500/10 text-red-500 border border-red-500/50 hover:bg-red-500 hover:text-white px-4 py-2 rounded-lg font-semibold transition-all flex items-center justify-center gap-2 text-sm"
                >
                  <Square className="fill-current w-4 h-4" />
                  Stop & Download
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

            {(status === 'Completed' || status === 'Interrupted') && (
              <div className="flex flex-col sm:flex-row justify-center pt-2 md:pt-4 gap-4">
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

      {/* How It Works Section */}
      <section className="bg-dark-800 p-6 md:p-8 rounded-xl border border-dark-700 shadow-xl space-y-8 mt-12">
        <div className="text-center space-y-2">
          <h2 className="text-2xl md:text-3xl font-extrabold text-white">How It Works 🚀</h2>
          <p className="text-gray-400 text-sm md:text-base max-w-xl mx-auto">Create highly engaging vertical quiz short videos in 3 simple steps.</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
          <div className="bg-dark-900/60 p-6 rounded-xl border border-dark-700/60 flex flex-col justify-between hover:border-brand-500/50 transition-all relative overflow-hidden group">
            <span className="absolute right-4 top-4 text-4xl font-extrabold text-dark-800 select-none group-hover:text-brand-500/10 transition-colors">01</span>
            <div className="space-y-3 z-10">
              <div className="w-10 h-10 rounded-lg bg-brand-500/10 border border-brand-500/25 flex items-center justify-center text-brand-400 text-lg">💡</div>
              <h3 className="text-base font-bold text-gray-200">Step 1: Choose Your Niche</h3>
              <p className="text-xs text-gray-400 leading-relaxed">Pick from high-retention categories like US Trivia, Mind Riddles, or Hollywood Quizzes.</p>
            </div>
          </div>
          
          <div className="bg-dark-900/60 p-6 rounded-xl border border-dark-700/60 flex flex-col justify-between hover:border-brand-500/50 transition-all relative overflow-hidden group">
            <span className="absolute right-4 top-4 text-4xl font-extrabold text-dark-800 select-none group-hover:text-brand-500/10 transition-colors">02</span>
            <div className="space-y-3 z-10">
              <div className="w-10 h-10 rounded-lg bg-brand-500/10 border border-brand-500/25 flex items-center justify-center text-brand-400 text-lg">🤖</div>
              <h3 className="text-base font-bold text-gray-200">Step 2: Automate Content</h3>
              <p className="text-xs text-gray-400 leading-relaxed">Our system automatically injects engaging visual progress bars, premium natural narration, and copyright-free backgrounds.</p>
            </div>
          </div>
          
          <div className="bg-dark-900/60 p-6 rounded-xl border border-dark-700/60 flex flex-col justify-between hover:border-brand-500/50 transition-all relative overflow-hidden group">
            <span className="absolute right-4 top-4 text-4xl font-extrabold text-dark-800 select-none group-hover:text-brand-500/10 transition-colors">03</span>
            <div className="space-y-3 z-10">
              <div className="w-10 h-10 rounded-lg bg-brand-500/10 border border-brand-500/25 flex items-center justify-center text-brand-400 text-lg">⚡</div>
              <h3 className="text-base font-bold text-gray-200">Step 3: 1-Click Export</h3>
              <p className="text-xs text-gray-400 leading-relaxed">Generate up to 100+ highly viral vertical quiz videos per day instantly to dominate your feed.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Frequently Asked Questions (FAQ) Accordion dropdown Section */}
      <section className="bg-dark-800 p-6 md:p-8 rounded-xl border border-dark-700 shadow-xl space-y-6 mt-12">
        <div className="text-center space-y-2">
          <h2 className="text-2xl md:text-3xl font-extrabold text-white">Frequently Asked Questions 💬</h2>
          <p className="text-gray-400 text-sm md:text-base max-w-xl mx-auto">Get answers to the most common questions about monetization, daily limits, and more.</p>
        </div>
        
        <div className="space-y-3 max-w-3xl mx-auto pt-4">
          {[
            {
              q: "Can I monetize these videos on Facebook and YouTube?",
              ans: "Yes! QuizViral AI generates fully compliance-friendly videos optimized for the Facebook Performance Bonus program, Instagram Reels, and YouTube Shorts monetization."
            },
            {
              q: "What is the daily cap for video generation?",
              ans: "Premium members can generate up to 100 high-quality vertical quiz videos every single day."
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
            <div key={idx} className="bg-dark-900 rounded-xl border border-dark-700/60 overflow-hidden transition-all">
              <button 
                onClick={() => setActiveFaq(activeFaq === idx ? null : idx)}
                className="w-full text-left px-5 py-4 flex items-center justify-between text-sm md:text-base font-bold text-gray-200 hover:bg-dark-800 transition-colors"
              >
                <span>{item.q}</span>
                <span className="text-brand-400 text-lg transition-transform duration-300 transform">
                  {activeFaq === idx ? '−' : '+'}
                </span>
              </button>
              
              {activeFaq === idx && (
                <div className="px-5 pb-5 pt-1 text-xs md:text-sm text-gray-400 border-t border-dark-800/80 leading-relaxed animate-in slide-in-from-top duration-300">
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
