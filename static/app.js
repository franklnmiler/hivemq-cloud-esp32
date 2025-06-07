// Menghubungkan WebSocket
const socket = io.connect('http://192.168.95.155:5002');
let suhuChart, kelembapanChart, tekananChart, intensitasCahayaChart; // Menambahkan chart untuk intensitas cahaya

// Fungsi untuk membuat chart
function createChart(ctx, label, data, borderColor, bgColor, satuan) {
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: label,
                data: data.data,
                borderColor: borderColor,
                backgroundColor: bgColor,
                fill: true,
                tension: 0.3,
                pointRadius: 3, // Ukuran titik pada grafik
                pointHoverRadius: 5, // Ukuran titik saat di-hover
                pointBackgroundColor: borderColor, // Warna titik sesuai garis
                pointBorderColor: '#fff', // Border putih untuk titik
                pointBorderWidth: 1 // Lebar border titik
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false, // Memungkinkan penyesuaian ukuran yang fleksibel
            plugins: {
                legend: { display: false }, // Sembunyikan legenda
                tooltip: { // Konfigurasi tooltip
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.7)',
                    titleFont: { size: 12 },
                    bodyFont: { size: 12 },
                    padding: 10,
                    cornerRadius: 6,
                    callbacks: {
                        label: function(context) {
                            // Tampilkan label dengan satuan
                            return context.dataset.label + ': ' + context.formattedValue + ' ' + satuan;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Waktu',
                        color: '#64748b' // Warna label sumbu X
                    },
                    grid: {
                        display: false // Sembunyikan garis grid vertikal
                    },
                    ticks: {
                        color: '#64748b' // Warna label tick sumbu X
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: satuan,
                        color: '#64748b' // Warna label sumbu Y
                    },
                    grid: {
                        color: '#e2e8f0' // Warna garis grid horizontal
                    },
                    ticks: {
                        color: '#64748b' // Warna label tick sumbu Y
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

// Fungsi untuk memperbarui tampilan data dan grafik
function updateCharts(data) {
    const waktu = new Date().toLocaleTimeString();
    const maxDataPoints = 20; // Batasi jumlah data di chart

    // --- Ringkasan Sensor ---
    // Pastikan nilai ada sebelum menampilkan dan format ke 2 desimal
    document.getElementById('suhu-terakhir').textContent = data.suhu ? data.suhu.toFixed(2) + ' °C' : '--';
    document.getElementById('kelembapan-terakhir').textContent = data.kelembapan ? data.kelembapan.toFixed(2) + ' %' : '--';
    document.getElementById('tekanan-terakhir').textContent = data.tekanan ? data.tekanan.toFixed(2) + ' hPa' : '--';
    document.getElementById('altitude-terakhir').textContent = data.altitude ? data.altitude.toFixed(2) + ' m' : '--';

    // Penanganan Jarak Ultrasonik
    if (data.jarak_ultrasonik !== undefined && data.jarak_ultrasonik !== null) {
        document.getElementById('shcr04-jarak').textContent = data.jarak_ultrasonik.toFixed(2) + ' cm';
    } else {
        document.getElementById('shcr04-jarak').textContent = '--';
    }

    // Intensitas Cahaya (BH1750) - BARU
    if (data.intensitas_cahaya !== undefined && data.intensitas_cahaya !== null) {
        document.getElementById('intensitas-cahaya-terakhir').textContent = data.intensitas_cahaya.toFixed(2) + ' Lux';
    } else {
        document.getElementById('intensitas-cahaya-terakhir').textContent = '--';
    }

    // Deteksi Kebakaran (menggunakan data.kebakaran langsung)
    let kebakaranStatus = '--';
    if (data.kebakaran !== undefined && data.kebakaran !== null) {
        // Asumsi: data.kebakaran adalah 0 untuk aman, 1 untuk bahaya
        kebakaranStatus = (data.kebakaran === 1 || data.kebakaran === '1') ? 'Bahaya' : 'Aman';
    }
    document.getElementById('kebakaran-terakhir').textContent = kebakaranStatus;

    // --- Update Waktu Terakhir Pembaruan & Animasi ---
    updateSensorTimestamp('suhu');
    updateSensorTimestamp('kelembapan');
    updateSensorTimestamp('tekanan');
    updateSensorTimestamp('altitude');
    updateSensorTimestamp('shcr04-jarak');
    updateSensorTimestamp('intensitas-cahaya'); // BARU
    updateSensorTimestamp('kebakaran');

    animateValueUpdate('suhu-terakhir');
    animateValueUpdate('kelembapan-terakhir');
    animateValueUpdate('tekanan-terakhir');
    animateValueUpdate('altitude-terakhir');
    animateValueUpdate('shcr04-jarak');
    animateValueUpdate('intensitas-cahaya-terakhir'); // BARU
    animateValueUpdate('kebakaran-terakhir');

    // --- Update Chart: Suhu ---
    if (suhuChart && suhuChart.data) {
        suhuChart.data.labels.push(waktu);
        suhuChart.data.datasets[0].data.push(data.suhu);
        if (suhuChart.data.labels.length > maxDataPoints) {
            suhuChart.data.labels.shift();
            suhuChart.data.datasets[0].data.shift();
        }
        suhuChart.update();
    }

    // --- Update Chart: Kelembapan ---
    if (kelembapanChart && kelembapanChart.data) {
        kelembapanChart.data.labels.push(waktu);
        kelembapanChart.data.datasets[0].data.push(data.kelembapan);
        if (kelembapanChart.data.labels.length > maxDataPoints) {
            kelembapanChart.data.labels.shift();
            kelembapanChart.data.datasets[0].data.shift();
        }
        kelembapanChart.update();
    }

    // --- Update Chart: Tekanan ---
    if (tekananChart && tekananChart.data) {
        tekananChart.data.labels.push(waktu);
        tekananChart.data.datasets[0].data.push(data.tekanan);
        if (tekananChart.data.labels.length > maxDataPoints) {
            tekananChart.data.labels.shift();
            tekananChart.data.datasets[0].data.shift();
        }
        tekananChart.update();
    }

    // --- Update Chart: Intensitas Cahaya (BH1750) - BARU ---
    if (intensitasCahayaChart && intensitasCahayaChart.data) {
        intensitasCahayaChart.data.labels.push(waktu);
        intensitasCahayaChart.data.datasets[0].data.push(data.intensitas_cahaya);
        if (intensitasCahayaChart.data.labels.length > maxDataPoints) {
            intensitasCahayaChart.data.labels.shift();
            intensitasCahayaChart.data.datasets[0].data.shift();
        }
        intensitasCahayaChart.update();
    }
}

// Fungsi untuk memuat data awal ke chart dari API
async function loadSensorChart() {
    try {
        const res = await fetch('/api/bme280/chart-multi');
        const data = await res.json();

        // Pastikan data.labels dan data sensor lainnya ada
        const labels = data.labels || [];
        const suhuData = data.suhu || [];
        const kelembapanData = data.kelembapan || [];
        const tekananData = data.tekanan || [];
        const intensitasCahayaData = data.intensitas_cahaya || []; // Data intensitas cahaya

        suhuChart = createChart(
            document.getElementById('chart-suhu').getContext('2d'),
            'Suhu (°C)', { labels: labels, data: suhuData },
            '#007bff', 'rgba(0,123,255,0.1)', '°C'
        );

        kelembapanChart = createChart(
            document.getElementById('chart-kelembapan').getContext('2d'),
            'Kelembapan (%)', { labels: labels, data: kelembapanData },
            '#28a745', 'rgba(40,167,69,0.1)', '%'
        );

        tekananChart = createChart(
            document.getElementById('chart-tekanan').getContext('2d'),
            'Tekanan (hPa)', { labels: labels, data: tekananData },
            '#ffc107', 'rgba(255,193,7,0.1)', 'hPa'
        );

        // Chart untuk Intensitas Cahaya (BH1750) - BARU
        intensitasCahayaChart = createChart(
            document.getElementById('chart-intensitas-cahaya').getContext('2d'),
            'Intensitas Cahaya (Lux)', { labels: labels, data: intensitasCahayaData },
            '#6f42c1', 'rgba(111,66,193,0.1)', 'Lux'
        );

    } catch (err) {
        console.error('Gagal memuat data chart awal:', err);
    }
}

// Fungsi untuk memperbarui timestamp sensor
function updateSensorTimestamp(sensorId) {
    const now = new Date();
    const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const element = document.getElementById(`${sensorId}-update-time`);
    if (element) {
        element.textContent = timeString;
    }
}

// Fungsi untuk menganimasikan pembaruan nilai
function animateValueUpdate(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.add('value-updated');
        setTimeout(() => {
            element.classList.remove('value-updated');
        }, 500); // Durasi animasi 0.5s
    }
}


// Jalankan saat halaman pertama kali dimuat
loadSensorChart();

// WebSocket listener untuk data baru
socket.on('new_data', function(data) {
    console.log('[WebSocket] Data Masuk:', data);
    updateCharts(data);
});

// WebSocket listener untuk notifikasi data yang dihapus
socket.on('data_cleaned', function(data) {
    const container = document.getElementById("notifikasi-container");
    const footer = document.getElementById("footer-info");

    if (data.mysql_deleted > 0 || data.firebase_deleted > 0) {
        const div = document.createElement("div");
        div.className = "bg-white rounded-lg shadow-lg p-4 border-l-4 border-red-500 notification-animation";
        div.innerHTML = `
          <div class="flex items-start">
            <div class="flex-shrink-0 p-2 bg-red-100 rounded-full text-red-500">
              <i class="fas fa-trash-alt"></i>
            </div>
            <div class="ml-3">
              <h4 class="text-sm font-medium text-gray-900">Pembersihan Data</h4>
              <p class="text-xs text-gray-500 mt-1">
                <strong>${data.mysql_deleted} data MySQL</strong> dan <strong>${data.firebase_deleted} data Firebase</strong> yang lebih lama dari ${data.threshold_minutes} menit telah dihapus pada <strong>${data.time}</strong>.
              </p>
            </div>
          </div>
        `;
        container.appendChild(div);
        footer.innerText = `Dihapus ${data.mysql_deleted} data MySQL dan ${data.firebase_deleted} data Firebase pada ${data.time}.`;
        setTimeout(() => div.remove(), 5000); // Hapus notifikasi setelah 5 detik
    } else {
        footer.innerText = "Tidak ada data yang dihapus.";
    }
});

// Fungsi untuk memperbarui waktu saat ini di header
function updateCurrentTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        timeElement.textContent = timeString;
    }
}
setInterval(updateCurrentTime, 1000); // Perbarui setiap detik
updateCurrentTime(); // Panggil sekali saat halaman dimuat

// Fungsi untuk membuat partikel latar belakang
function createParticles() {
    const particlesContainer = document.getElementById('particles');
    const particleCount = 15;

    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.classList.add('particle');

        // Ukuran acak antara 5 dan 15px
        const size = Math.random() * 10 + 5;
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;

        // Posisi acak
        particle.style.left = `${Math.random() * 100}%`;
        particle.style.top = `${Math.random() * 100}%`;

        // Durasi animasi acak antara 10s dan 20s
        particle.style.animationDuration = `${Math.random() * 10 + 10}s`;

        // Penundaan animasi acak
        particle.style.animationDelay = `${Math.random() * 5}s`;

        particlesContainer.appendChild(particle);
    }
}

// Inisialisasi partikel saat DOM siap
document.addEventListener('DOMContentLoaded', createParticles);


// Fungsi untuk menambahkan efek riak pada tombol
function setupRippleEffect() {
    const buttons = document.querySelectorAll('.ripple');

    buttons.forEach(button => {
        button.style.position = 'relative';
        button.style.overflow = 'hidden';

        button.addEventListener('click', function(e) {
            const rect = e.target.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const ripples = document.createElement('span');
            ripples.style.position = 'absolute';
            ripples.style.background = 'rgba(255, 255, 255, 0.5)';
            ripples.style.borderRadius = '50%';
            ripples.style.transform = 'scale(0)';
            ripples.style.animation = 'ripple-animation 0.6s linear';
            ripples.style.left = `${x}px`;
            ripples.style.top = `${y}px`;
            ripples.style.width = ripples.style.height = '200px';
            ripples.style.pointerEvents = 'none';
            ripples.style.zIndex = '10';
            ripples.classList.add('ripple-span');

            this.appendChild(ripples);

            setTimeout(() => {
                ripples.remove();
            }, 600); // sama dengan durasi animasi
        });
    });
}

// Tambahkan CSS animasi riak
const rippleStyle = document.createElement('style');
rippleStyle.innerHTML = `
@keyframes ripple-animation {
  to {
    transform: scale(4);
    opacity: 0;
  }
}
.value-updated {
    transition: background-color 0.5s ease-out;
    background-color: #e0f2fe; /* Warna latar belakang saat diperbarui */
}
`;
document.head.appendChild(rippleStyle);

// Panggil fungsi setelah DOM siap
document.addEventListener('DOMContentLoaded', setupRippleEffect);
