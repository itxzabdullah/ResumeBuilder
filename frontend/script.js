document.addEventListener("DOMContentLoaded", () => {
  // ============================================
  // GLOBAL UI INTERACTIONS
  // ============================================
  
  const inputs = document.querySelectorAll(".form-control");
  inputs.forEach((input) => {
    input.addEventListener("focus", () => input.parentElement.classList.add("focused"));
    input.addEventListener("blur", () => input.parentElement.classList.remove("focused"));
  });

  // ============================================
  // UPLOAD PAGE LOGIC
  // ============================================
  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("fileInput");
  const uploadProgress = document.getElementById("uploadProgress");
  const progressBar = uploadProgress?.querySelector(".progress-bar");
  const progressText = document.getElementById("progressText");
  const uploadSuccess = document.getElementById("uploadSuccess");

  if (dropZone && fileInput) {
    dropZone.addEventListener("click", () => fileInput.click());
    dropZone.addEventListener("dragover", (e) => { e.preventDefault(); dropZone.classList.add("dragover"); });
    dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
    dropZone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropZone.classList.remove("dragover");
      if (e.dataTransfer.files.length) handleFileUpload(e.dataTransfer.files[0]);
    });
    fileInput.addEventListener("change", () => {
      if (fileInput.files.length) handleFileUpload(fileInput.files[0]);
    });
  }

  async function handleFileUpload(file) {
    const validTypes = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"];
    if (!validTypes.includes(file.type)) return alert("Please upload a PDF, DOCX, or TXT file.");

    if (dropZone) dropZone.classList.add("d-none");
    if (uploadProgress) uploadProgress.classList.remove("d-none");
    if (document.getElementById("fileName")) document.getElementById("fileName").innerText = file.name;

    const formData = new FormData();
    formData.append("resume", file);

    try {
      let progress = 0;
      const interval = setInterval(() => {
        progress += 10;
        if (progressBar) progressBar.style.width = `${progress}%`;
        if (progressText) progressText.innerText = `${progress}%`;
        if (progress >= 90) clearInterval(interval);
      }, 100);

      // --- PRODUCTION URL LOGIC (Critical for Mobile) ---
      const apiUrl = window.location.hostname.includes("localhost") || window.location.hostname.includes("127.0.0.1")
                     ? "/upload_resume" 
                     : "https://onlyjobs-five.vercel.app/upload_resume";

      const response = await fetch(apiUrl, { method: "POST", body: formData });
      clearInterval(interval);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Upload failed");
      }

      const data = await response.json();
      if (progressBar) progressBar.style.width = "100%";
      if (progressText) progressText.innerText = "100%";

      // --- STATE MANAGEMENT ---
      // We save the AI results locally so the dashboard can load them instantly
      localStorage.setItem("resumeData", JSON.stringify({
          skills: data.skills || [],
          ats_score: data.ats_score || 0,
          ats_breakdown: data.ats_breakdown || {},
          improvements: data.improvements || [],
          resume_text: data.resume_text || "",
          experience_level: data.experience_level || "Mid",
          recommended_jobs: data.recommended_jobs || [] 
      }));

      if (uploadSuccess) uploadSuccess.classList.remove("d-none");
      setTimeout(() => { window.location.href = "dashboard.html"; }, 1500);

    } catch (error) {
      console.error("Upload error:", error);
      alert(`Upload failed: ${error.message}`);
      if (dropZone) dropZone.classList.remove("d-none");
      if (uploadProgress) uploadProgress.classList.add("d-none");
    }
  }

  // ============================================
  // DASHBOARD LOGIC
  // ============================================
  if (window.location.pathname.includes("dashboard")) {
    const storedData = localStorage.getItem("resumeData");
    if (storedData) {
      const resumeData = JSON.parse(storedData);
      
      // Render components using data from the 10k dataset
      if (resumeData.ats_score) animateATSScore(resumeData.ats_score);
      if (resumeData.ats_breakdown) updateBars(resumeData.ats_breakdown);
      if (resumeData.improvements) updateImprovementList(resumeData.improvements);
      
      // Load matched jobs
      if (resumeData.recommended_jobs && resumeData.recommended_jobs.length > 0) {
        renderJobs(resumeData.recommended_jobs);
      } else {
        fetchNewRecommendations(resumeData);
      }
    }
  }

  function animateATSScore(target) {
    const el = document.getElementById("atsScoreDisplay");
    if (!el) return;
    let curr = 0;
    const t = setInterval(() => {
      curr++;
      el.textContent = curr;
      if (curr >= target) clearInterval(t);
    }, 15);
  }

  function updateBars(b) {
    const map = { 
      'skillMatchBar': b.skill_match, 
      'textSimBar': b.text_similarity, 
      'expMatchBar': b.experience_match 
    };
    for (let [id, val] of Object.entries(map)) {
      const el = document.getElementById(id);
      if (el) el.style.width = `${val}%`;
    }
  }

  function updateImprovementList(imps) {
    const list = document.getElementById("improvementsList");
    if (!list) return;
    list.innerHTML = imps.map(i => `
      <div class="list-group-item bg-transparent border-0 d-flex gap-2 py-2">
        <i class="bi bi-patch-check-fill text-primary"></i>
        <div class="small"><strong>${i.title || 'Analysis'}:</strong> ${i.description || i}</div>
      </div>
    `).join('');
  }

  function renderJobs(jobs) {
    const container = document.getElementById("jobMatchesContainer");
    if (!container) return;
    
    container.innerHTML = jobs.slice(0, 5).map(j => `
      <div class="job-item p-3 mb-2 rounded border bg-white shadow-sm transition-hover">
        <div class="d-flex justify-content-between align-items-center">
          <span class="fw-bold small text-truncate" style="max-width: 60%;">${j.job_title}</span>
          <span class="badge rounded-pill bg-primary-subtle text-primary">
            ${Math.round(j.match_score || j.combined_score || 0)}% Match
          </span>
        </div>
        <div class="extra-small text-muted mb-2">${j.company} • ${j.location}</div>
        
        <button class="btn btn-sm btn-outline-primary w-100 btn-interview-trigger" data-job="${j.job_title}">
          <i class="bi bi-chat-dots me-1"></i> Interview Prep
        </button>
      </div>
    `).join('');
  }

  async function fetchNewRecommendations(r) {
    const url = window.location.hostname.includes("localhost") ? "/job_recommendations" : "https://onlyjobs-five.vercel.app/job_recommendations";
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ skills: r.skills, resume_text: r.resume_text, experience_level: r.experience_level })
    });
    if (res.ok) {
      const d = await res.json();
      renderJobs(d.recommended_jobs || []);
    }
  }

  const jobContainer = document.getElementById("jobMatchesContainer");
  
  if (jobContainer) {
    jobContainer.addEventListener("click", async (e) => {
      // Check if the clicked element (or its parent) is our trigger button
      const btn = e.target.closest(".btn-interview-trigger");
      if (!btn) return;

      const jobTitle = btn.getAttribute("data-job");
      
      // Visual feedback: show loading state on button
      const originalText = btn.innerHTML;
      btn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Loading...`;
      btn.disabled = true;

      const apiUrl = window.location.hostname.includes("localhost") || window.location.hostname.includes("127.0.0.1")
                     ? "/get_questions" 
                     : "https://onlyjobs-five.vercel.app/get_questions";

      try {
        const response = await fetch(apiUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ job_title: jobTitle })
        });

        if (response.ok) {
          const data = await response.json();
          
          // Save result to localStorage for the interview page to pick up
          localStorage.setItem("currentInterviewJob", jobTitle);
          localStorage.setItem("interviewQuestions", JSON.stringify(data.questions));

          // Redirect to the interview page
          window.location.href = "interview.html";
        } else {
          throw new Error("Failed to load questions");
        }
      } catch (error) {
        console.error("Interview Error:", error);
        alert("Could not generate interview questions. Please try again.");
        btn.innerHTML = originalText;
        btn.disabled = false;
      }
    });
  }
  if (window.location.pathname.includes("interview")) {
    const qData = localStorage.getItem("interviewQuestions");
    const targetJob = localStorage.getItem("currentInterviewJob");
    
    if (qData && targetJob) {
      const questions = JSON.parse(qData);
      
      // Set the header
      const header = document.getElementById("interviewHeader");
      if (header) header.innerText = `Interview Preparation: ${targetJob}`;

      // Function to render lists
      const fillList = (id, list) => {
        const el = document.getElementById(id);
        if (el && list) {
          el.innerHTML = list.map(q => `<li class="list-group-item bg-transparent"><i class="bi bi-question-circle me-2 text-primary"></i>${q}</li>`).join('');
        }
      };

      // Fill technical, behavioral, and situational lists
      // Make sure these IDs match your interview.html IDs
      fillList("techQuestionsList", questions.technical);
      fillList("behavioralQuestionsList", questions.behavioral);
      fillList("situationalQuestionsList", questions.situational);
    }
  }
}
);