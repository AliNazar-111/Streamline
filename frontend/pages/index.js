import { useState, useEffect } from "react";
import axios from "axios";
import ReactPlayer from "react-player";
import Head from "next/head";

export default function Home() {
  const [scriptFile, setScriptFile] = useState(null);
  const [voiceFile, setVoiceFile] = useState(null);
  const [genre, setGenre] = useState("Documentary");
  const [competitorUrl, setCompetitorUrl] = useState("");
  
  const [pexelsKey, setPexelsKey] = useState("");
  const [pixabayKey, setPixabayKey] = useState("");
  const [geminiKey, setGeminiKey] = useState("");
  const [geminiEndpoint, setGeminiEndpoint] = useState("");
  const [aspectRatio, setAspectRatio] = useState("16:9");
  const [voiceName, setVoiceName] = useState("Female (Default)");
  const [bgMusicFile, setBgMusicFile] = useState(null);
  const [bgMusicVolume, setBgMusicVolume] = useState(0.1);
  
  const [loading, setLoading] = useState(false);
  const [checkingGemini, setCheckingGemini] = useState(false);
  const [checkingPexels, setCheckingPexels] = useState(false);
  const [checkingPixabay, setCheckingPixabay] = useState(false);
  
  const [videoUrl, setVideoUrl] = useState("");
  const [systemStatus, setSystemStatus] = useState({ 
    device: "Checking...", 
    gpu_available: false,
    cpu_usage: 0,
    memory_usage: 0,
    gpu_stats: { name: "None", load: 0, memory: 0 }
  });
  const [keyStatus, setKeyStatus] = useState({ gemini: false, pexels: false, pixabay: false });

  // Fetch system status periodically
  useEffect(() => {
    const fetchStatus = () => {
      axios.get("http://localhost:8000/system-status")
        .then(res => setSystemStatus(res.data))
        .catch(err => console.error("Failed to fetch system status", err));
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  // Validate keys when they change (debounce could be better, but simple effect for now)
  useEffect(() => {
    const validate = async () => {
      if (!geminiKey && !pexelsKey && !pixabayKey) return;
      
      const formData = new FormData();
      formData.append("api_key_gemini", geminiKey);
      formData.append("api_endpoint_gemini", geminiEndpoint);
      formData.append("api_key_pexels", pexelsKey);
      formData.append("api_key_pixabay", pixabayKey);
      
      try {
        const res = await axios.post("http://localhost:8000/validate-keys", formData);
        setKeyStatus(res.data);
      } catch (e) {
        console.error("Key validation failed", e);
      }
    };
    
    const timeout = setTimeout(validate, 1000); // Debounce 1s
    return () => clearTimeout(timeout);
  }, [geminiKey, geminiEndpoint, pexelsKey, pixabayKey]);

  const handleSubmit = async () => {
    if (!scriptFile) {
      alert("Please upload a script file");
      return;
    }

    const formData = new FormData();
    formData.append("script", scriptFile);
    if (voiceFile) {
      formData.append("voiceover", voiceFile);
    }
    formData.append("competitor_url", competitorUrl);
    formData.append("base_genre", genre);
    formData.append("api_key_pexels", pexelsKey);
    formData.append("api_key_pixabay", pixabayKey);
    formData.append("api_key_gemini", geminiKey);
    formData.append("api_endpoint_gemini", geminiEndpoint);
    formData.append("api_endpoint_gemini", geminiEndpoint);
    formData.append("aspect_ratio", aspectRatio);
    formData.append("voice_name", voiceName);
    if (bgMusicFile) {
      formData.append("background_music", bgMusicFile);
      formData.append("bg_music_volume", bgMusicVolume);
    }

    setLoading(true);
    try {
      const response = await axios.post(
        "http://localhost:8000/generate-video",
        formData,
        {
          responseType: "blob",
          headers: { "Content-Type": "multipart/form-data" },
        }
      );

      const videoBlob = new Blob([response.data], { type: "video/mp4" });
      const url = URL.createObjectURL(videoBlob);
      setVideoUrl(url);
    } catch (err) {
      console.error(err);
      alert("Error generating video");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 text-white font-sans selection:bg-purple-500 selection:text-white">
      <Head>
        <title>AutoVideo | Video Generator</title>
        <meta name="description" content="Generate videos automatically with AI" />
      </Head>

      <main className="container mx-auto px-4 py-12 max-w-6xl">
        <header className="text-center mb-12">
          <h1 className="text-5xl font-extrabold tracking-tight mb-4 bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-600">
            AutoVideo 🎬
          </h1>
          <p className="text-gray-400 text-lg">
            Turn your scripts and voiceovers into engaging videos in seconds.
          </p>
          
          {/* System Status Dashboard */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl mx-auto mt-8">
            {/* Device Info */}
            <div className="bg-gray-800/60 border border-gray-700 p-4 rounded-xl backdrop-blur-sm flex flex-col items-center justify-center">
               <span className="text-gray-400 text-xs uppercase tracking-wider mb-1">Rendering Engine</span>
               <div className="flex items-center gap-2">
                 <div className={`w-2 h-2 rounded-full ${systemStatus.gpu_available ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' : 'bg-yellow-500'}`}></div>
                 <span className="font-mono font-bold text-sm">{systemStatus.device}</span>
               </div>
            </div>

            {/* Load Stats */}
            <div className="bg-gray-800/60 border border-gray-700 p-4 rounded-xl backdrop-blur-sm flex justify-around items-center">
               <div className="text-center">
                 <span className="text-gray-400 text-xs uppercase tracking-wider block mb-1">CPU Load</span>
                 <span className={`font-mono font-bold text-xl ${systemStatus.cpu_usage > 80 ? 'text-red-400' : 'text-blue-400'}`}>{systemStatus.cpu_usage}%</span>
               </div>
               <div className="w-px h-8 bg-gray-700"></div>
               <div className="text-center">
                 <span className="text-gray-400 text-xs uppercase tracking-wider block mb-1">GPU Load</span>
                 <span className={`font-mono font-bold text-xl ${systemStatus.gpu_stats.load > 80 ? 'text-red-400' : 'text-purple-400'}`}>{systemStatus.gpu_stats.load}%</span>
               </div>
            </div>

            {/* API Status */}
            <div className="bg-gray-800/60 border border-gray-700 p-4 rounded-xl backdrop-blur-sm flex flex-col justify-center gap-2">
               <div className="flex justify-between items-center px-2">
                 <span className="text-xs text-gray-400">Gemini</span>
                 <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${keyStatus.gemini ? 'bg-green-900/50 text-green-400 border border-green-800' : 'bg-gray-700 text-gray-500'}`}>
                   {keyStatus.gemini ? 'ACTIVE' : 'INACTIVE'}
                 </span>
               </div>
               <div className="flex justify-between items-center px-2">
                 <span className="text-xs text-gray-400">Stock APIs</span>
                 <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${keyStatus.pexels || keyStatus.pixabay ? 'bg-green-900/50 text-green-400 border border-green-800' : 'bg-gray-700 text-gray-500'}`}>
                   {keyStatus.pexels || keyStatus.pixabay ? 'READY' : 'MISSING'}
                 </span>
               </div>
            </div>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">
          {/* Form Section */}
          <div className="bg-gray-800/50 backdrop-blur-sm p-8 rounded-2xl border border-gray-700 shadow-xl">
            <h2 className="text-2xl font-semibold mb-6 text-purple-300">Configuration</h2>
            
            <div className="space-y-6">
              {/* File Uploads */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Script File (.txt)</label>
                  <input
                    type="file"
                    accept=".txt"
                    onChange={(e) => setScriptFile(e.target.files[0])}
                    className="block w-full text-sm text-gray-400
                      file:mr-4 file:py-2 file:px-4
                      file:rounded-full file:border-0
                      file:text-sm file:font-semibold
                      file:bg-purple-600 file:text-white
                      hover:file:bg-purple-700
                      cursor-pointer bg-gray-900/50 rounded-lg border border-gray-600 focus:outline-none focus:border-purple-500 transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Voiceover File (.mp3) <span className="text-gray-500 text-xs">(Optional - AI Voice used if empty)</span>
                  </label>
                  <input
                    type="file"
                    accept=".mp3"
                    onChange={(e) => setVoiceFile(e.target.files[0])}
                    className="block w-full text-sm text-gray-400
                      file:mr-4 file:py-2 file:px-4
                      file:rounded-full file:border-0
                      file:text-sm file:font-semibold
                      file:bg-purple-600 file:text-white
                      hover:file:bg-purple-700
                      cursor-pointer bg-gray-900/50 rounded-lg border border-gray-600 focus:outline-none focus:border-purple-500 transition-colors"
                  />
                </div>
              </div>

              {/* Audio Settings */}
              <div className="space-y-4 pt-4 border-t border-gray-700">
                 <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Audio Settings</h3>
                 
                 {!voiceFile && (
                   <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">AI Voice</label>
                      <select 
                        value={voiceName} 
                        onChange={(e) => setVoiceName(e.target.value)}
                        className="w-full bg-gray-900/50 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500 transition-colors"
                      >
                        <option>Male (Default)</option>
                        <option>Female (Default)</option>
                        <option>Islamic (Male)</option>
                        <option>Islamic (Female)</option>
                        <option>Deep (Male)</option>
                      </select>
                   </div>
                 )}

                 <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Background Music / Nasheed <span className="text-gray-500 text-xs">(Optional)</span>
                    </label>
                    <input
                      type="file"
                      accept=".mp3,.wav"
                      onChange={(e) => setBgMusicFile(e.target.files[0])}
                      className="block w-full text-sm text-gray-400
                        file:mr-4 file:py-2 file:px-4
                        file:rounded-full file:border-0
                        file:text-sm file:font-semibold
                        file:bg-purple-600 file:text-white
                        hover:file:bg-purple-700
                        cursor-pointer bg-gray-900/50 rounded-lg border border-gray-600 focus:outline-none focus:border-purple-500 transition-colors"
                    />
                 </div>
              </div>

              {/* Settings */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Genre</label>
                  <select 
                    value={genre} 
                    onChange={(e) => setGenre(e.target.value)}
                    className="w-full bg-gray-900/50 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500 transition-colors"
                  >
                    <option>Documentary</option>
                    <option>Financial/Tech</option>
                    <option>Storytime</option>
                    <option>Vlog</option>
                    <option>Cartoon</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Competitor URL</label>
                  <input
                    placeholder="Optional"
                    value={competitorUrl}
                    onChange={(e) => setCompetitorUrl(e.target.value)}
                    className="w-full bg-gray-900/50 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                  />
                </div>
              </div>

              {/* API Keys */}
              <div className="space-y-4 pt-4 border-t border-gray-700">
                <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">API Keys (Optional)</h3>
                
                {/* Pexels */}
                <div className="flex gap-2">
                  <input
                    placeholder="Pexels API Key"
                    value={pexelsKey}
                    onChange={(e) => setPexelsKey(e.target.value)}
                    className="flex-1 bg-gray-900/50 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                  />
                  <button
                    onClick={() => {
                       setCheckingPexels(true);
                       const formData = new FormData();
                       formData.append("api_key_pexels", pexelsKey);
                       axios.post("http://localhost:8000/validate-keys", formData)
                         .then(res => setKeyStatus(prev => ({...prev, pexels: res.data.pexels})))
                         .finally(() => setCheckingPexels(false));
                    }}
                    disabled={checkingPexels}
                    className="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors min-w-[80px]"
                  >
                    {checkingPexels ? "..." : "Check"}
                  </button>
                </div>

                {/* Pixabay */}
                <div className="flex gap-2">
                  <input
                    placeholder="Pixabay API Key"
                    value={pixabayKey}
                    onChange={(e) => setPixabayKey(e.target.value)}
                    className="flex-1 bg-gray-900/50 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                  />
                  <button
                    onClick={() => {
                       setCheckingPixabay(true);
                       const formData = new FormData();
                       formData.append("api_key_pixabay", pixabayKey);
                       axios.post("http://localhost:8000/validate-keys", formData)
                         .then(res => setKeyStatus(prev => ({...prev, pixabay: res.data.pixabay})))
                         .finally(() => setCheckingPixabay(false));
                    }}
                    disabled={checkingPixabay}
                    className="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors min-w-[80px]"
                  >
                    {checkingPixabay ? "..." : "Check"}
                  </button>
                </div>

                {/* Gemini */}
                <div className="space-y-2">
                    <div className="flex gap-2">
                      <input
                        type="password"
                        placeholder="Gemini API Key (Optional - For Smart Features)"
                        value={geminiKey}
                        onChange={(e) => setGeminiKey(e.target.value)}
                        className="flex-1 bg-gray-900/50 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                      />
                      <button
                        onClick={() => {
                           setCheckingGemini(true);
                           const formData = new FormData();
                           formData.append("api_key_gemini", geminiKey);
                           formData.append("api_endpoint_gemini", geminiEndpoint);
                           axios.post("http://localhost:8000/validate-keys", formData)
                             .then(res => setKeyStatus(prev => ({...prev, gemini: res.data.gemini})))
                             .catch(err => console.error("Gemini check failed", err))
                             .finally(() => setCheckingGemini(false));
                        }}
                        disabled={checkingGemini}
                        className="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors min-w-[80px]"
                      >
                        {checkingGemini ? "..." : "Check"}
                      </button>
                    </div>
                    <input
                        placeholder="Gemini API Endpoint (Optional - e.g. https://my-proxy.com)"
                        value={geminiEndpoint}
                        onChange={(e) => setGeminiEndpoint(e.target.value)}
                        className="w-full bg-gray-900/50 border border-gray-600 rounded-lg px-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                      />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Aspect Ratio</label>
                  <select 
                    value={aspectRatio} 
                    onChange={(e) => setAspectRatio(e.target.value)}
                    className="w-full bg-gray-900/50 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500 transition-colors"
                  >
                    <option value="16:9">Landscape (16:9) - YouTube</option>
                    <option value="9:16">Vertical (9:16) - Reels/Shorts</option>
                  </select>
                </div>
              </div>

              <button
                onClick={handleSubmit}
                disabled={loading}
                className={`w-full py-3 px-6 rounded-xl font-bold text-lg shadow-lg transition-all transform hover:scale-[1.02] active:scale-[0.98] ${
                  loading
                    ? "bg-gray-600 cursor-not-allowed text-gray-300"
                    : "bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white"
                }`}
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Rendering Video...
                  </span>
                ) : (
                  "Initialize Render"
                )}
              </button>
            </div>
          </div>

          {/* Preview Section */}
          <div className="flex flex-col gap-6">
            <div className="bg-gray-800/50 backdrop-blur-sm p-8 rounded-2xl border border-gray-700 shadow-xl min-h-[400px] flex flex-col items-center justify-center text-center">
              {videoUrl ? (
                <div className="w-full space-y-4 animate-in fade-in duration-500">
                  <h2 className="text-2xl font-semibold text-green-400 mb-4">Video Generated! 🎉</h2>
                  <div className="relative pt-[56.25%] bg-black rounded-lg overflow-hidden shadow-2xl border border-gray-600">
                    <ReactPlayer 
                      url={videoUrl} 
                      controls 
                      width="100%" 
                      height="100%" 
                      className="absolute top-0 left-0"
                    />
                  </div>
                  <a 
                    href={videoUrl} 
                    download="autovideo.mp4"
                    className="inline-block mt-4 px-6 py-3 bg-green-600 hover:bg-green-500 text-white font-semibold rounded-lg transition-colors"
                  >
                    Download Final Video
                  </a>
                </div>
              ) : (
                <div className="text-gray-500 space-y-4">
                  <div className="w-24 h-24 bg-gray-700/50 rounded-full flex items-center justify-center mx-auto mb-4">
                    <span className="text-4xl">🎬</span>
                  </div>
                  <h3 className="text-xl font-medium text-gray-300">Ready to Generate</h3>
                  <p className="max-w-xs mx-auto">
                    Upload your script and voiceover, configure your settings, and hit render to see the magic happen.
                  </p>
                </div>
              )}
            </div>
            
            {/* Instructions / Tips */}
            <div className="bg-blue-900/20 border border-blue-800/50 p-6 rounded-xl">
              <h4 className="text-blue-400 font-semibold mb-2 flex items-center gap-2">
                <span className="text-xl">💡</span> Pro Tip
              </h4>
              <p className="text-blue-200/80 text-sm">
                For best results, ensure your script matches the length of your voiceover. 
                Add API keys for Pexels or Pixabay to get high-quality stock footage instead of placeholders.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
