document.addEventListener('DOMContentLoaded', () => {
  const fileInput = document.getElementById('fileInput');
  const uploadZone = document.getElementById('uploadZone');
  const preview = document.getElementById('preview');
  const featureSelect = document.getElementById('feature');
  const valueBox = document.getElementById('valueBox');
  const valueSlider = document.getElementById('valueSlider');
  const valueLabel = document.getElementById('valueLabel');
  const valDisplay = document.getElementById('val');
  const processBtn = document.getElementById('processBtn');
  const msg = document.getElementById('msg');
  const resultImg = document.getElementById('result');
  const resultPlaceholder = document.getElementById('resultPlaceholder');
  const downloadBtn = document.getElementById('downloadBtn');
  const btnText = processBtn.querySelector('.btn-text');
  const btnLoader = processBtn.querySelector('.btn-loader');

  let selectedFile = null;

  // Features that need a slider (UPDATED WITH NEW FEATURES)
  const sliderFeatures = {
    brightness: { label: 'Brightness', min: 0.3, max: 2.5, step: 0.1, value: 1.0 },
    contrast:   { label: 'Contrast',   min: 0.3, max: 2.5, step: 0.1, value: 1.0 },
    saturation: { label: 'Saturation', min: 0.0, max: 2.5, step: 0.1, value: 1.0 },
    warmth:     { label: 'Warmth Level', min: 0.5, max: 1.5, step: 0.1, value: 1.0 },
    hue:        { label: 'Hue Shift',  min: -10, max: 10, step: 1, value: 0 },
    gaussian:   { label: 'Kernel Size', min: 3, max: 21, step: 2, value: 5 },
    median:     { label: 'Kernel Size', min: 3, max: 15, step: 2, value: 5 },
    mean:       { label: 'Kernel Size', min: 3, max: 15, step: 2, value: 5 },
    unsharp:    { label: 'Strength',   min: 0.5, max: 2.0, step: 0.1, value: 1.0 },
    posterize:  { label: 'Levels',     min: 2, max: 8, step: 1, value: 4 },
    pixelate:   { label: 'Block Size', min: 1, max: 5, step: 1, value: 3 },
  };

  // Upload Zone
  uploadZone.addEventListener('click', () => fileInput.click());

  uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('dragover');
  });

  uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('dragover');
  });

  uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
      handleFile(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) {
      handleFile(e.target.files[0]);
    }
  });

  function handleFile(file) {
    if (!file.type.startsWith('image/')) {
      msg.textContent = 'Please select a valid image file.';
      msg.style.color = '#ef4444'; // Red error color
      return;
    }
    selectedFile = file;
    preview.src = URL.createObjectURL(file);
    preview.style.display = 'block';
    uploadZone.style.display = 'none';
    msg.textContent = ''; // Clear previous messages
  }

  // Feature change → show/hide slider
  featureSelect.addEventListener('change', () => {
    const feat = featureSelect.value;
    if (sliderFeatures[feat]) {
      const cfg = sliderFeatures[feat];
      valueLabel.textContent = cfg.label;
      valueSlider.min = cfg.min;
      valueSlider.max = cfg.max;
      valueSlider.step = cfg.step;
      valueSlider.value = cfg.value;
      valDisplay.textContent = cfg.value;
      valueBox.style.display = 'block';
    } else {
      valueBox.style.display = 'none';
    }
  });

  // Trigger once on load
  featureSelect.dispatchEvent(new Event('change'));

  valueSlider.addEventListener('input', () => {
    valDisplay.textContent = valueSlider.value;
  });

  // Process Image
  processBtn.addEventListener('click', async () => {
    if (!selectedFile) {
      msg.textContent = 'Please upload an image first.';
      msg.style.color = '#ef4444'; // Red error
      return;
    }

    const feature = featureSelect.value;

    // UI Loading State
    processBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline-flex'; // changed to inline-flex for icon alignment
    msg.textContent = '';
    msg.style.color = '#fbbf24'; // Yellow loading color

    const formData = new FormData();
    formData.append('image', selectedFile);
    formData.append('feature', feature);
    formData.append('value', valueSlider.value);

    try {
      const res = await fetch('/process', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();

      if (!res.ok || data.error) {
        msg.textContent = data.error || 'Something went wrong.';
        msg.style.color = '#ef4444'; // Red error
        return;
      }

      // Show Result
      resultPlaceholder.style.display = 'none';
      resultImg.src = data.result_url + '?t=' + Date.now();
      resultImg.style.display = 'block';

      // Setup Download
      downloadBtn.href = data.result_url;
      downloadBtn.style.display = 'flex';

      msg.textContent = '✓ Done! Ready to download.';
      msg.style.color = '#34d399'; // Green success
    } catch (err) {
      msg.textContent = 'Network error. Please try again.';
      msg.style.color = '#ef4444';
    } finally {
      // Reset UI
      processBtn.disabled = false;
      btnText.style.display = 'inline-flex';
      btnLoader.style.display = 'none';
    }
  });
});
