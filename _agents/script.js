// ===== Closure to track successful submissions =====
const submissionCounter = (() => {
  let count = 0;
  return () => {
    count++;
    return count;
  };
})();

// ===== Arrow function validation (HW requirement) =====
const validateForm = () => {
  const content = document.getElementById("content").value.trim();
  const termsChecked = document.getElementById("terms").checked;

  if (content.length <= 25) {
    alert("Blog content should be more than 25 characters");
    return false;
  }

  if (!termsChecked) {
    alert("You must agree to the terms and conditions");
    return false;
  }

  return true;
};

// ===== Nice UI helpers (optional, does NOT break HW rules) =====
const $ = (id) => document.getElementById(id);

const setInlineError = (msg) => {
  const box = $("inlineError");
  if (!msg) {
    box.style.display = "none";
    box.textContent = "";
    return;
  }
  box.style.display = "block";
  box.textContent = msg;
};

const updatePreview = () => {
  const title = $("title").value.trim();
  const author = $("author").value.trim();
  const email = $("email").value.trim();
  const content = $("content").value;
  const category = $("category").value;

  $("previewTitle").textContent = title || "Your blog title will appear here";
  $("previewMeta").textContent = `By ${author || "Your Name"} • ${email || "your@email.com"}`;
  $("previewCategory").textContent = category;

  $("kvTitle").textContent = title || "—";
  $("kvAuthor").textContent = author || "—";
  $("kvEmail").textContent = email || "—";
  $("kvCategory").textContent = category || "—";

  $("previewContent").textContent = content.trim() ? content : "Start typing to see your content preview…";

  $("charCount").textContent = content.length.toString();
};

// live updates
["title", "author", "email", "content", "category"].forEach((id) => {
  $(id).addEventListener("input", () => {
    setInlineError("");
    updatePreview();
  });
});

// reset button
$("resetBtn").addEventListener("click", () => {
  $("blogForm").reset();
  setInlineError("");
  updatePreview();
});

// initial preview render
updatePreview();

// ===== Form submit (HW requirements) =====
$("blogForm").addEventListener("submit", (event) => {
  event.preventDefault();

  // Keep HW alerts exactly
  if (!validateForm()) {
    // Optional inline hint (not required)
    const contentLen = $("content").value.trim().length;
    if (contentLen <= 25) setInlineError("Content must be more than 25 characters.");
    else if (!$("terms").checked) setInlineError("You must agree to the terms and conditions.");
    return;
  }

  // Collect form data
  const formData = {
    title: $("title").value.trim(),
    author: $("author").value.trim(),
    email: $("email").value.trim(),
    content: $("content").value,
    category: $("category").value
  };

  // 2) Convert to JSON string and log
  const jsonString = JSON.stringify(formData);
  console.log("JSON String:", jsonString);

  // Parse to object
  const parsedData = JSON.parse(jsonString);

  // 3) Object destructuring (title, email) and log
  const { title, email } = parsedData;
  console.log("Title:", title);
  console.log("Email:", email);

  // 4) Spread operator to add submissionDate and log
  const updatedParsed = {
    ...parsedData,
    submissionDate: new Date().toISOString()
  };
  console.log("Updated Object:", updatedParsed);

  // 5) Closure counter
  const count = submissionCounter();
  console.log("Submission Count:", count);

  // Optional UI message
  setInlineError("");
  alert("Blog published! Check the console for JSON output.");
});

