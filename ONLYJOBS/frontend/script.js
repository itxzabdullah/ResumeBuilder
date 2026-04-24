document.addEventListener("DOMContentLoaded", () => {
  // ============================================
  // GLOBAL UI INTERACTIONS
  // ============================================
  
  // Input focus effects
  const inputs = document.querySelectorAll(".form-control");
  inputs.forEach((input) => {
    input.addEventListener("focus", () => {
      input.parentElement.classList.add("focused");
    });
    input.addEventListener("blur", () => {
      input.parentElement.classList.remove("focused");
    });
  });

  // Toggle Password Visibility (If login is present)
  const togglePassword = document.querySelector("#togglePassword");
  const passwordInput = document.querySelector("#password");
  if (togglePassword && passwordInput) {
    const toggleIcon = togglePassword.querySelector("i");
    togglePassword.addEventListener("click", function () {
      const type = passwordInput.getAttribute("type") === "password" ? "text" : "password";
      passwordInput.setAttribute("type", type);
      if (type === "text") {
        toggleIcon.classList.remove("bi-eye-slash");
        toggleIcon.classList.add("bi-eye");
      } else {
        toggleIcon.classList.remove("bi-eye");
        toggleIcon.classList.add("bi-eye-slash");
      }
    });
  }

  // ============================================
  // LOGIN LOGIC
  // ============================================
  const loginForm = document.getElementById("loginForm");

  if (loginForm) {
    loginForm.addEventListener("submit", (event) => {
        event.preventDefault();
        if (!loginForm.checkValidity()) {
          event.stopPropagation();
          loginForm.classList.add("was-validated");
          return;
        }

        const submitBtn = loginForm.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Logging in...';

        setTimeout(() => {
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<i class="bi bi-check-circle-fill"></i> Success!';
          submitBtn.classList.remove("btn-gradient");
          submitBtn.classList.add("btn-success");

          setTimeout(() => {
            window.location.href = "dashboard.html";
          }, 1000);
        }, 1500);
      }, false);
  }

  // ============================================
  // UPLOAD PAGE
  // ============================================
  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("fileInput");
  const uploadProgress = document.getElementById("uploadProgress");
  const progressBar = uploadProgress?.querySelector(".progress-bar");
  const progressText = document.getElementById("progressText");
  const uploadSuccess = document.getElementById("uploadSuccess");

  if (dropZone && fileInput) {
    dropZone.addEventListener("click", () => fileInput.click());

    dropZone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropZone.classList.add("dragover");
    });

    dropZone.addEventListener("dragleave", () => {
      dropZone.classList.remove("dragover");
    });

    dropZone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropZone.classList.remove("dragover");
      const files = e.dataTransfer.files;
      if (files.length) handleFileUpload(files[0]);
    });

    fileInput.addEventListener("change", () => {
      if (fileInput.files.length) handleFileUpload(fileInput.files[0]);
    });
  }

  // Backend Upload Function
  async function handleFileUpload(file) {
    const validTypes = [
      "application/pdf", 
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
      "text/plain"
    ];
    
    if (!validTypes.includes(file.type)) {
      alert("Please upload a PDF, DOCX, or TXT file.");
      return;
    }

    // UI Updates
    if (dropZone) dropZone.classList.add("d-none");
    if (uploadProgress) uploadProgress.classList.remove("d-none");
    
    const fileNameEl = document.getElementById("fileName");
    if(fileNameEl) fileNameEl.innerText = file.name;

    const formData = new FormData();
    formData.append("resume", file);

    try {
      // Simulation for smooth UI
      let progress = 0;
      const interval = setInterval(() => {
        progress += 10;
        if (progressBar) progressBar.style.width = `${progress}%`;
        if (progressText) progressText.innerText = `${progress}%`;
        if (progress >= 90) clearInterval(interval);
      }, 100);

      // Actual API Call
      const response = await fetch("/upload_resume", {
        method: "POST",
        body: formData,
      });

      clearInterval(interval);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Upload failed");
      }

      const data = await response.json();

      // Complete progress
      if (progressBar) progressBar.style.width = "100%";
      if (progressText) progressText.innerText = "100%";

      // Save to Storage
      localStorage.setItem("resumeData", JSON.stringify({
          skills: data.skills || [],
          ats_score: data.ats_score || 0,
          ats_breakdown: data.ats_breakdown || {},
          improvements: data.improvements || [],
          resume_text: data.resume_text || "",
          experience_level: data.experience_level || "Mid",
      }));

      if (uploadSuccess) uploadSuccess.classList.remove("d-none");

      setTimeout(() => {
        window.location.href = "dashboard.html";
      }, 1500);

    } catch (error) {
      console.error("Upload error:", error);
      alert(`Failed to upload resume: ${error.message}`);
      if (dropZone) dropZone.classList.remove("d-none");
      if (uploadProgress) uploadProgress.classList.add("d-none");
      if (progressBar) progressBar.style.width = "0%";
    }
  }

  // ============================================
  // DASHBOARD LOGIC
  // ============================================
  if (window.location.pathname.includes("dashboard")) {
    loadDashboardData();
    
    // Handle Browse Jobs click
    const browseJobsLink = document.querySelector('.browse-jobs-link');
    if (browseJobsLink) {
      browseJobsLink.addEventListener('click', (e) => {
        e.preventDefault();
        const jobsTab = document.querySelector('[data-bs-target="#jobs"]');
        if (jobsTab) {
          jobsTab.click();
        }
      });
    }
  }

  async function loadDashboardData() {
    try {
      const storedData = localStorage.getItem("resumeData");
      if (!storedData) {
        const container = document.getElementById("jobMatchesContainer");
        if(container) {
          container.innerHTML = '<div class="text-center py-4"><p class="text-muted">No resume data found. <a href="upload.html" class="text-decoration-none">Upload a resume</a> to see matches.</p></div>';
        }
        return;
      }

      const resumeData = JSON.parse(storedData);

      // 1. Update ATS Score
      if (resumeData.ats_score !== undefined) {
        animateATSScore(resumeData.ats_score);
      }

      // 2. Update Improvements
      if (resumeData.improvements && resumeData.improvements.length > 0) {
        updateImprovements(resumeData.improvements);
      }

      // 3. Update ATS Breakdown (Visual bars)
      if (resumeData.ats_breakdown) {
          updateATSBreakdown(resumeData.ats_breakdown);
      }

      // 4. Fetch Job Recommendations
      const response = await fetch("/job_recommendations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          skills: resumeData.skills,
          resume_text: resumeData.resume_text,
          experience_level: resumeData.experience_level,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log("Job recommendations response:", data);
        
        // Fixed: Use 'recommended_jobs' field from backend response
        const jobs = data.recommended_jobs || [];
        updateJobMatches(jobs);
      } else {
        console.error("Failed to fetch job recommendations");
        const container = document.getElementById("jobMatchesContainer");
        if(container) {
          container.innerHTML = '<div class="text-center py-4"><p class="text-muted">Unable to load job matches. Please try again later.</p></div>';
        }
      }
    } catch (error) {
      console.error("Dashboard load error:", error);
      const container = document.getElementById("jobMatchesContainer");
      if(container) {
        container.innerHTML = '<div class="text-center py-4"><p class="text-danger">Error loading dashboard data.</p></div>';
      }
    }
  }

  function animateATSScore(targetScore) {
    const scoreElement = document.getElementById("atsScoreDisplay");
    if (!scoreElement) return;

    let currentScore = 0;
    const increment = Math.ceil(targetScore / 50);
    const timer = setInterval(() => {
      currentScore += increment;
      if (currentScore >= targetScore) {
        currentScore = targetScore;
        clearInterval(timer);
      }
      scoreElement.textContent = Math.round(currentScore);
    }, 30);
  }

  function updateImprovements(improvements) {
    const improvementsList = document.getElementById("improvementsList");
    if (!improvementsList) return;

    improvementsList.innerHTML = "";
    const icons = [
      "bi-exclamation-circle-fill text-danger", 
      "bi-info-circle-fill text-info", 
      "bi-lightbulb-fill text-warning", 
      "bi-check-circle-fill text-success"
    ];

    improvements.forEach((improvement, index) => {
        const iconClass = icons[index % icons.length];
        const div = document.createElement("div");
        div.className = "list-group-item bg-transparent px-0 py-3 d-flex gap-3 align-items-start border-bottom-0";
        div.innerHTML = `
            <i class="bi ${iconClass} mt-1"></i>
            <div>
                <h6 class="mb-1 fw-semibold">${improvement.title || "Optimization Tip"}</h6>
                <p class="mb-0 text-muted small">${improvement.description || improvement}</p>
            </div>
        `;
        improvementsList.appendChild(div);
    });
  }

  function updateJobMatches(jobs) {
    const container = document.getElementById("jobMatchesContainer");
    if (!container) return;

    container.innerHTML = "";
    
    if (!jobs || jobs.length === 0) {
        container.innerHTML = '<div class="text-center py-4"><p class="text-muted">No job matches found. Try updating your resume with more skills.</p></div>';
        return;
    }

    jobs.slice(0, 3).forEach((job) => {
        const matchScore = Math.round(job.match_score || job.combined_score || 0);
        const matchColor = matchScore >= 80 ? "success" : matchScore >= 60 ? "primary" : "secondary";
        
        const div = document.createElement("div");
        div.className = "job-item p-3 mb-3 rounded-3 bg-light-subtle border";
        div.innerHTML = `
            <div class="d-flex justify-content-between mb-2">
                <span class="fw-bold">${job.job_title || "Position"}</span>
                <span class="badge bg-${matchColor}">${matchScore}% Match</span>
            </div>
            <p class="text-muted small mb-1">${job.company || "Company"} • ${job.location || "Location"}</p>
            ${job.salary ? `<p class="text-muted small mb-0">💰 ${job.salary}</p>` : ''}
        `;
        container.appendChild(div);
    });
    
    // Add view all link
    const viewAll = document.createElement("div");
    viewAll.className = "text-center mt-3";
    viewAll.innerHTML = `<button class="btn btn-link text-decoration-none fw-medium small" onclick="document.querySelector('[data-bs-target=\\'#jobs\\']').click()">View All ${jobs.length} Matches <i class="bi bi-arrow-right"></i></button>`;
    container.appendChild(viewAll);
    
    // Update badge
    const badge = document.getElementById("newJobsBadge");
    if(badge) badge.innerText = `${jobs.length} New`;
  }

  function updateATSBreakdown(breakdown) {
    // Update skill match
    if(document.getElementById('skillMatchPercent')) {
        const sm = Math.round(breakdown.skill_match || 0);
        document.getElementById('skillMatchPercent').innerText = `${sm}%`;
        document.getElementById('skillMatchBar').style.width = `${sm}%`;
    }
    
    // Update text similarity if element exists
    if(document.getElementById('textSimPercent')) {
        const ts = Math.round(breakdown.text_similarity || 0);
        document.getElementById('textSimPercent').innerText = `${ts}%`;
        document.getElementById('textSimBar').style.width = `${ts}%`;
    }
    
    // Update experience match if element exists
    if(document.getElementById('expMatchPercent')) {
        const em = Math.round(breakdown.experience_match || 0);
        document.getElementById('expMatchPercent').innerText = `${em}%`;
        document.getElementById('expMatchBar').style.width = `${em}%`;
    }
  }

  // ============================================
  // BUILDER WIZARD
  // ============================================
  const resumeForm = document.getElementById('resumeForm');
  if (resumeForm) {
      let currentStep = 1;
      const totalSteps = 4;
      const formSteps = document.querySelectorAll('.wizard-step');
      const stepIndicators = document.querySelectorAll('.step-indicator');
      const prevBtn = document.getElementById('prevBtn');
      const nextBtn = document.getElementById('nextBtn');

      function updateStep(step) {
          formSteps.forEach(s => {
              s.classList.add('d-none');
              if (parseInt(s.dataset.step) === step) s.classList.remove('d-none');
          });
          
          stepIndicators.forEach(i => {
              const s = parseInt(i.dataset.step);
              i.classList.remove('active');
              if (s <= step) i.classList.add('active');
          });
          
          if(prevBtn) prevBtn.disabled = step === 1;
          
          if(nextBtn) {
              if (step === totalSteps) {
                  nextBtn.innerHTML = '<i class="bi bi-download me-2"></i>Finish & Download';
              } else {
                  const nextStepLabels = ['Experience', 'Education', 'Skills', 'Download'];
                  nextBtn.innerHTML = `Next: ${nextStepLabels[step - 1]} <i class="bi bi-arrow-right ms-1"></i>`;
              }
          }
          
          currentStep = step;
      }

      if(nextBtn) {
          nextBtn.addEventListener('click', () => {
              if (currentStep < totalSteps) {
                  updateStep(currentStep + 1);
              } else {
                  alert('Resume complete! In a full version, this would generate and download your resume.');
              }
          });
      }

      if(prevBtn) {
          prevBtn.addEventListener('click', () => {
              if (currentStep > 1) updateStep(currentStep - 1);
          });
      }

      // Live Preview Updates
      resumeForm.addEventListener('input', (e) => {
          const name = e.target.name;
          const val = e.target.value;
          
          // Update name
          if (name === 'firstName' || name === 'lastName') {
              const f = resumeForm.querySelector('[name="firstName"]')?.value || '';
              const l = resumeForm.querySelector('[name="lastName"]')?.value || '';
              const el = document.getElementById('previewName');
              if(el) el.innerText = `${f} ${l}`.trim() || 'John Doe';
          }
          
          // Update job title
          if(name === 'jobTitle') {
             const el = document.getElementById('previewTitle');
             if(el) el.innerText = val || 'Professional Title';
          }
          
          // Update email
          if(name === 'email') {
             const el = document.getElementById('previewEmail');
             if(el) {
                 const icon = '<i class="bi bi-envelope-fill text-muted opacity-50"></i>';
                 el.innerHTML = `${icon} ${val || 'john@example.com'}`;
             }
          }
          
          // Update phone
          if(name === 'phone') {
             const el = document.getElementById('previewPhone');
             if(el) {
                 const icon = '<i class="bi bi-telephone-fill text-muted opacity-50"></i>';
                 el.innerHTML = `${icon} ${val || '+1 (555) 000-0000'}`;
             }
          }
          
          // Update location
          if(name === 'location') {
             const el = document.getElementById('previewLocation');
             if(el) {
                 const icon = '<i class="bi bi-geo-alt-fill text-muted opacity-50"></i>';
                 el.innerHTML = `${icon} ${val || 'New York, USA'}`;
             }
          }
          
          // Update summary
          if(name === 'summary') {
             const el = document.getElementById('previewSummary');
             if(el) el.innerText = val || 'Experienced professional with a passion for excellence...';
          }
      });
  }
});