import { useState } from "react";
import axios from "axios";
import ReactPlayer from "react-player";

export default function Home() {
  const [scriptFile, setScriptFile] = useState(null);
  const [voiceFile, setVoiceFile] = useState(null);
  const [genre, setGenre] = useState("Documentary");
  const [competitorUrl, setCompetitorUrl] = useState("");
  const [pexelsKey, setPexelsKey] = useState("");
  const [pixabayKey, setPixabayKey] = useState("");
  const [videoUrl, setVideoUrl] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!scriptFile || !voiceFile) {
      alert("Please upload both script and voiceover files");
      return;
    }

    const formData = new FormData();
    formData.append("script", scriptFile);
    formData.append("voiceover", voiceFile);
    formData.append("competitor_url", competitorUrl);
    formData.append("base_genre", genre);
    formData.append("api_key_pexels", pexelsKey);
    formData.append("api_key_pixabay", pixabayKey);

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
    <main style={{ padding: "2rem", textAlign: "center" }}>
      <h1>AutoVideo 🎬</h1>

      <div style={{ marginBottom: "1rem" }}>
        <input
          type="file"
          accept=".txt"
          onChange={(e) => setScriptFile(e.target.files[0])}
        />{" "}
        <br />
        <input
          type="file"
          accept=".mp3"
          onChange={(e) => setVoiceFile(e.target.files[0])}
        />{" "}
        <br />
        <input
          placeholder="Competitor URL"
          value={competitorUrl}
          onChange={(e) => setCompetitorUrl(e.target.value)}
        />{" "}
        <br />
        <select value={genre} onChange={(e) => setGenre(e.target.value)}>
          <option>Documentary</option>
          <option>Financial/Tech</option>
          <option>Storytime</option>
          <option>Vlog</option>
        </select>{" "}
        <br />
        <input
          placeholder="Pexels API Key"
          value={pexelsKey}
          onChange={(e) => setPexelsKey(e.target.value)}
        />{" "}
        <br />
        <input
          placeholder="Pixabay API Key"
          value={pixabayKey}
          onChange={(e) => setPixabayKey(e.target.value)}
        />{" "}
        <br />
        <button onClick={handleSubmit} disabled={loading}>
          {loading ? "Rendering..." : "Initialize Render"}
        </button>
      </div>

      {videoUrl && (
        <div>
          <ReactPlayer url={videoUrl} controls height="480px" width="820px" />
          <a href={videoUrl} download="autovideo.mp4">
            Download Final Video
          </a>
        </div>
      )}
    </main>
  );
}
