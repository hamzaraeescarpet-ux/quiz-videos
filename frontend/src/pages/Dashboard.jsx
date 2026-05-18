import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, Play, Square, Download, Trash2, Plus, Image as ImageIcon } from 'lucide-react';
import { motion } from 'framer-motion';

export default function Dashboard() {
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [rows, setRows] = useState([{ id: 1, question: '', option1: '', option2: '', option3: '', option4: '', answer: '' }]);
  const [logoFile, setLogoFile] = useState(null);
  
  const [sessionId, setSessionId] = useState(null);
  const [status, setStatus] = useState(null); // 'Processing', 'Completed', 'Interrupted', 'Failed'
  const [progress, setProgress] = useState({ current: 0, total: 0 });

  useEffect(() => {
    // Dynamic fetching from backend
    axios.get('/api/categories').then(res => {
      setCategories(res.data.categories || []);
      if (res.data.categories && res.data.categories.length > 0) {
        setSelectedCategory(res.data.categories[0]);
      }
    }).catch(err => console.error("Error fetching categories", err));
  }, []);

  useEffect(() => {
    let interval;
    if (sessionId && status === 'Processing') {
      interval = setInterval(() => {
        axios.get(`/api/status/${sessionId}`).then(res => {
          setStatus(res.data.status);
          setProgress({ current: res.data.completed_so_far, total: res.data.total_expected });
        }).catch(err => console.error(err));
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [sessionId, status]);

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

  const handleCSVUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
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
        if (parsedRows.length > 0) {
          setRows(parsedRows.slice(0, 100)); // Max 100
        }
      };
      reader.readAsText(file);
    }
  };

  const startGeneration = async () => {
    const isValid = rows.every(r => r.question && r.option1 && r.option2 && r.option3 && r.option4 && r.answer);
    if (!isValid) return alert("Please fill all fields in the rows.");
    
    if (rows.length > 5) {
      const wantsPremium = window.confirm("Free tier limits you to 5 videos. Proceed with only 5?");
      if (!wantsPremium) return;
      setRows(rows.slice(0, 5));
    }

    const formData = new FormData();
    formData.append('questions', JSON.stringify(rows));
    formData.append('category', selectedCategory);
    if (logoFile) {
      formData.append('logo', logoFile);
    }

    try {
      setStatus('Processing');
      setProgress({ current: 0, total: rows.length });
      const res = await axios.post('/api/generate-bulk', formData);
      setSessionId(res.data.session_id);
    } catch (err) {
      console.error(err);
      alert("Failed to start generation.");
      setStatus(null);
    }
  };

  const stopGeneration = async () => {
    if (sessionId) {
      try {
        await axios.post(`/api/stop-generation/${sessionId}`);
        setStatus('Interrupted');
      } catch (err) {
        console.error(err);
      }
    }
  };

  const downloadZip = () => {
    window.location.href = `/api/download/${sessionId}`;
  };

  return (
    <div className="space-y-6 md:space-y-8 animate-in fade-in duration-500">
      <header className="px-2">
        <h1 className="text-2xl md:text-3xl font-extrabold mb-2">Create Viral Videos</h1>
        <p className="text-gray-400 text-sm md:text-base">Transform text into highly engaging trivia short videos instantly.</p>
      </header>

      {/* Step 1: Category */}
      <section className="bg-dark-800 p-4 md:p-6 rounded-xl border border-dark-700 shadow-xl">
        <h2 className="text-lg md:text-xl font-semibold mb-4 text-brand-300">1. Choose Template Category</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {categories.length > 0 ? categories.map(cat => (
            <div 
              key={cat} 
              onClick={() => setSelectedCategory(cat)}
              className={`cursor-pointer p-4 rounded-lg border-2 transition-all duration-300 flex flex-col items-center justify-center gap-2
                ${selectedCategory === cat ? 'border-brand-500 bg-brand-900/30' : 'border-dark-600 bg-dark-700 hover:border-brand-400/50 hover:bg-dark-600'}
              `}
            >
              <div className="w-12 h-12 rounded-full bg-dark-800 flex items-center justify-center text-xl shadow-inner">
                {cat === 'Minecraft' ? '⛏️' : cat === 'Satisfying' ? '🫧' : cat === 'Nature' ? '🌲' : cat === 'Space' ? '🚀' : '✨'}
              </div>
              <span className="font-medium text-sm text-center">{cat}</span>
            </div>
          )) : (
            <div className="col-span-full text-center text-gray-500 py-4">No categories found.</div>
          )}
        </div>
      </section>

      {/* Step 2: Data & Media */}
      <section className="bg-dark-800 p-4 md:p-6 rounded-xl border border-dark-700 shadow-xl space-y-6 md:space-y-8">
        <h2 className="text-lg md:text-xl font-semibold text-brand-300">2. Input Data & Branding</h2>
        
        {/* Branding */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Upload Custom Logo (Optional)</label>
          <div 
            {...getLogoProps()} 
            className="border-2 border-dashed border-dark-600 rounded-xl p-6 md:p-8 text-center cursor-pointer hover:border-brand-500 transition-colors bg-dark-900/50 flex flex-col items-center justify-center"
          >
            <input {...getLogoInputProps()} />
            <ImageIcon className="mx-auto h-10 w-10 md:h-12 md:w-12 text-gray-400 mb-3" />
            {logoFile ? (
              <p className="text-brand-400 font-medium text-sm md:text-base break-all">Selected: {logoFile.name}</p>
            ) : (
              <p className="text-gray-400 text-sm md:text-base">Tap or drag a custom logo here</p>
            )}
          </div>
        </div>

        {/* Data Table */}
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <h3 className="font-medium text-gray-200">Questions Data</h3>
            <div className="flex w-full sm:w-auto items-center gap-3">
              <label className="flex-1 sm:flex-none cursor-pointer bg-dark-700 hover:bg-dark-600 text-white px-3 py-2 md:py-1.5 rounded-md text-sm md:text-sm transition-colors flex items-center justify-center gap-2">
                <UploadCloud className="w-4 h-4" />
                Upload CSV
                <input type="file" accept=".csv" className="hidden" onChange={handleCSVUpload} />
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
            Generate Bulk Videos
          </button>
        ) : (
          <div className="w-full space-y-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <h3 className="text-base md:text-lg font-bold text-brand-300">
                  {status === 'Processing' ? 'Rendering in progress...' : status === 'Completed' ? 'Generation Complete!' : 'Generation Interrupted'}
                </h3>
                <p className="text-gray-400 text-sm">
                  {progress.current} of {progress.total} videos generated
                </p>
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
            <div className="w-full bg-dark-900 rounded-full h-3 md:h-4 overflow-hidden shadow-inner">
              <motion.div 
                className="bg-gradient-to-r from-brand-500 to-blue-500 h-3 md:h-4"
                initial={{ width: 0 }}
                animate={{ width: `${progress.total > 0 ? (progress.current / progress.total) * 100 : 0}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>

            {(status === 'Completed' || status === 'Interrupted') && (
              <div className="flex justify-center pt-2 md:pt-4">
                <button 
                  onClick={downloadZip}
                  className="w-full sm:w-auto bg-green-600 hover:bg-green-500 text-white px-6 md:px-8 py-3 rounded-xl font-bold text-base md:text-lg transition-all shadow-lg shadow-green-600/20 flex items-center justify-center gap-2"
                >
                  <Download className="w-5 h-5" />
                  Download ZIP
                </button>
              </div>
            )}
            {status === 'Failed' && (
              <div className="mt-4 p-4 bg-red-900/50 border border-red-500/50 rounded-lg text-white">
                <h3 className="font-bold text-red-400 mb-2">Generation Failed!</h3>
                <p className="text-sm">Please visit <a href="/api/logs" target="_blank" className="underline text-blue-300">this link</a> to see the exact error.</p>
                <button onClick={() => setStatus(null)} className="mt-3 px-4 py-2 bg-dark-700 hover:bg-dark-600 rounded text-sm">Try Again</button>
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
