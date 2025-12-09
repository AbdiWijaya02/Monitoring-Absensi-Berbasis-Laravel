<div class="container" wire:poll.10s>
    
    <div class="row mb-4">
        <div class="col-md-4">
            <div class="card text-white bg-success mb-3 shadow h-100">
                <div class="card-header bg-success border-0">Hadir (Range Ini)</div>
                <div class="card-body d-flex justify-content-between align-items-center">
                    <h2 class="card-title fw-bold mb-0">{{ $hadirCount }}</h2>
                    <i class="fas fa-user-check fa-3x opacity-50"></i>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card text-white bg-danger mb-3 shadow h-100">
                <div class="card-header bg-danger border-0">Tidak Hadir / Izin</div>
                <div class="card-body d-flex justify-content-between align-items-center">
                    <h2 class="card-title fw-bold mb-0">{{ $tidakHadirCount }}</h2>
                    <i class="fas fa-user-times fa-3x opacity-50"></i>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card bg-white mb-3 shadow h-100">
                <div class="card-header bg-white fw-bold">Performa Kehadiran</div>
                <div class="card-body">
                    <h4 class="text-center mb-2">{{ $persentase }}%</h4>
                    <div class="progress" style="height: 20px;">
                        <div class="progress-bar {{ $persentase >= 80 ? 'bg-success' : ($persentase >= 50 ? 'bg-warning' : 'bg-danger') }}" 
                        role="progressbar" 
                        style="<?php echo 'width: ' . $persentase . '%'; ?>"
                        aria-valuenow="{{ $persentase }}" 
                        aria-valuemin="0" 
                        aria-valuemax="100">
                    </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="row mb-4">
        <div class="col-md-8">
            <div class="card shadow-sm h-100">
                <div class="card-header bg-white fw-bold"><i class="fas fa-filter me-1"></i> Filter Realtime</div>
                <div class="card-body">
                    <div class="row g-2">
                        <div class="col-md-6">
                            <label class="small fw-bold">Dari Tanggal</label>
                            <input type="date" wire:model.live="startDate" class="form-control">
                        </div>
                        <div class="col-md-6">
                            <label class="small fw-bold">Sampai Tanggal</label>
                            <input type="date" wire:model.live="endDate" class="form-control">
                        </div>
                    </div>

                    @if(in_array(Auth::user()->role, ['admin', 'dosen']))
                    <div class="row g-2 mt-2">
                        <div class="col-md-6">
                            <label class="small fw-bold">Filter PBL</label>
                            <select wire:model.live="filterPbl" class="form-select">
                                <option value="">-- Semua PBL --</option>
                                @foreach($pblOptions as $pbl)
                                    <option value="{{ $pbl }}">{{ $pbl }}</option>
                                @endforeach
                            </select>
                        </div>
                        <div class="col-md-6">
                            <label class="small fw-bold">Filter Angkatan</label>
                            <select wire:model.live="filterAngkatan" class="form-select">
                                <option value="">-- Semua Angkatan --</option>
                                @foreach($angkatanOptions as $angk)
                                    <option value="{{ $angk }}">{{ $angk }}</option>
                                @endforeach
                            </select>
                        </div>
                    </div>
                    @endif
                    
                    <div class="mt-4 d-flex align-items-center">
                        <button wire:click="exportExcel" class="btn btn-success btn-sm me-2">
                            <i class="fas fa-file-excel"></i> Export Excel
                        </button>
                        <button wire:click="downloadPDF" class="btn btn-danger btn-sm me-2">
                            <i class="fas fa-file-pdf"></i> Export PDF
                        </button>
                        <span wire:loading class="text-primary small">
                            <i class="fas fa-spinner fa-spin"></i> Memuat data...
                        </span>
                    </div>
                </div>
            </div>
        </div>

        <div class="col-md-4">
            <div class="card shadow-sm h-100">
                <div class="card-header bg-white fw-bold">Rasio Kehadiran</div>
                <div class="card-body">
                    <div wire:ignore>
                        <canvas id="pieChart" style="max-height: 200px;"></canvas>
                    </div>
                </div>
            </div>
        </div>
    </div>

    @if(in_array(Auth::user()->role, ['admin', 'dosen']))
    <div class="row mb-4">
        <div class="col-md-12">
            <div class="card shadow-sm">
                <div class="card-header bg-white fw-bold">Ranking Kehadiran per Tim PBL (Top 10)</div>
                <div class="card-body">
                    <div wire:ignore>
                        <canvas id="barChart" style="height: 100px; max-height: 300px;"></canvas>
                    </div>
                </div>
            </div>
        </div>
    </div>
    @endif

    <div class="card shadow-sm mb-5">
        <div class="card-body p-0">
            <div class="table-responsive">
                <table class="table table-striped table-hover mb-0 align-middle text-nowrap">
                    <thead class="table-secondary text-center">
                        <tr>
                            <th>Tanggal</th>
                            <th>NIM</th>
                            <th>Nama</th>
                            <th>PBL</th>
                            <th>Foto</th>
                            <th>Status</th>
                            <th>Masuk</th>
                            <th>Pulang</th>
                            <th>Durasi</th>
                        </tr>
                    </thead>
                    <tbody>
                        @forelse($data_absen as $absen)
                        <tr>
                            <td class="text-center small">{{ \Carbon\Carbon::parse($absen->tanggal)->format('d/m/Y') }}</td>
                            <td class="text-center fw-bold">{{ $absen->NIM }}</td>
                            <td>{{ $absen->Nama }}</td>
                            <td class="text-center"><span class="badge bg-light text-dark border">{{ $absen->PBL }}</span></td>
                            
                            <td class="text-center">
                                @if($absen->bukti_foto)
                                    <button type="button" class="btn btn-sm btn-outline-primary" data-bs-toggle="modal" data-bs-target="#fotoModal{{ $absen->id }}">
                                        <i class="fas fa-camera"></i>
                                    </button>
                                    
                                    <div class="modal fade" id="fotoModal{{ $absen->id }}" tabindex="-1" aria-hidden="true" wire:ignore.self>
                                        <div class="modal-dialog modal-dialog-centered">
                                            <div class="modal-content">
                                                <div class="modal-header">
                                                    <h5 class="modal-title">Bukti Kehadiran</h5>
                                                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                                </div>
                                                <div class="modal-body text-center">
                                                    <img src="{{ asset('storage/'.$absen->bukti_foto) }}" class="img-fluid rounded">
                                                    <p class="mt-2 text-muted">{{ $absen->Nama }}</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                @else <span class="text-muted">-</span> @endif
                            </td>

                            <td class="text-center">
                                @if($absen->status_kehadiran == 'Hadir')
                                    <span class="badge bg-success">Hadir</span>
                                @elseif($absen->status_kehadiran == 'Sakit')
                                    <span class="badge bg-warning text-dark">Sakit</span>
                                @elseif($absen->status_kehadiran == 'Izin')
                                    <span class="badge bg-info text-dark">Izin</span>
                                @else
                                    <span class="badge bg-danger">Alpha</span>
                                @endif
                            </td>
                            <td class="text-center">{{ $absen->absen_hadir ? \Carbon\Carbon::parse($absen->absen_hadir)->format('H:i') : '-' }}</td>
                            <td class="text-center">{{ $absen->absen_pulang ? \Carbon\Carbon::parse($absen->absen_pulang)->format('H:i') : '-' }}</td>
                            <td class="text-center">{{ $absen->durasi_kerja ?? '-' }}</td>
                        </tr>
                        @empty
                        <tr><td colspan="9" class="text-center py-4 text-muted">Data Kosong</td></tr>
                        @endforelse
                    </tbody>
                </table>
            </div>
        </div>
        <div class="card-footer bg-white">
            {{ $data_absen->links() }} 
        </div>
    </div>

    <script>
        document.addEventListener('livewire:initialized', () => {
            
            // --- 1. INISIALISASI PIE CHART ---
            const ctxPie = document.getElementById('pieChart');
            let pieChart;
            if (ctxPie) {
                pieChart = new Chart(ctxPie, {
                    type: 'doughnut',
                    data: {
                        labels: ['Hadir', 'Tidak Hadir'],
                        datasets: [{
                            data: [0, 0], // Data awal kosong, nunggu update
                            backgroundColor: ['#198754', '#dc3545'],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { position: 'bottom' } }
                    }
                });
            }

            // --- 2. INISIALISASI BAR CHART (GRAFIK BATANG) ---
            const ctxBar = document.getElementById('barChart');
            let barChart;
            if (ctxBar) {
                barChart = new Chart(ctxBar, {
                    type: 'bar',
                    data: {
                        labels: [], // Label PBL
                        datasets: [{
                            label: 'Jumlah Mahasiswa Hadir',
                            data: [],
                            backgroundColor: '#0d6efd', // Warna Biru
                            borderColor: '#0a58ca',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: { stepSize: 1 } // Agar angka bulat (orang)
                            }
                        }
                    }
                });
            }

            // --- 3. MENERIMA DATA DARI LIVEWIRE ---
            Livewire.on('update-chart', (data) => {
                const stats = data[0]; 

                // Update Pie Chart
                if (pieChart) {
                    pieChart.data.datasets[0].data = [stats.hadir, stats.tidakHadir];
                    pieChart.update();
                }

                // Update Bar Chart
                if (barChart && stats.pblLabels) {
                    barChart.data.labels = stats.pblLabels;
                    barChart.data.datasets[0].data = stats.pblData;
                    barChart.update();
                }
            });
        });
    </script>
</div>