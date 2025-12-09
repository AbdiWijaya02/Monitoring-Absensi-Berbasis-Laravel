<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Manajemen Izin & Sakit</title>
    <link rel="icon" href="{{ asset('images/logobrail.jpg') }}" type="image/jpg">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body class="bg-light">

    <nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4">
        <div class="container">
            <a class="navbar-brand" href="{{ route('monitoring.index') }}">AIoT Monitoring</a>
            <div class="d-flex text-white">
                <a href="{{ route('monitoring.index') }}" class="btn btn-outline-light btn-sm me-2">Kembali ke Dashboard</a>
            </div>
        </div>
    </nav>

    <div class="container">
        
        @if(session('success'))
            <div class="alert alert-success">{{ session('success') }}</div>
        @endif

        <div class="row">
            @if(Auth::user()->role == 'user')
            <div class="col-md-4">
                <div class="card shadow-sm">
                    <div class="card-header bg-primary text-white">Form Pengajuan</div>
                    <div class="card-body">
                        <form action="{{ route('izin.store') }}" method="POST" enctype="multipart/form-data">
                            @csrf
                            <div class="mb-3">
                                <label class="form-label">Tanggal</label>
                                <input type="date" name="tanggal" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Jenis</label>
                                <select name="jenis_izin" class="form-select" required>
                                    <option value="Sakit">Sakit</option>
                                    <option value="Izin">Izin (Urusan Penting)</option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Keterangan</label>
                                <textarea name="keterangan" class="form-control" rows="3" required></textarea>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Bukti (Surat Dokter/Foto)</label>
                                <input type="file" name="bukti_dokumen" class="form-control">
                                <small class="text-muted">Format: JPG, PNG (Max 2MB)</small>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">Kirim Pengajuan</button>
                        </form>
                    </div>
                </div>
            </div>
            @endif

            <div class="{{ Auth::user()->role == 'user' ? 'col-md-8' : 'col-md-12' }}">
                <div class="card shadow-sm">
                    <div class="card-header bg-white fw-bold">
                        {{ Auth::user()->role == 'user' ? 'Riwayat Pengajuan Saya' : 'Daftar Pengajuan Masuk' }}
                    </div>
                    <div class="card-body p-0">
                        <table class="table table-striped mb-0 align-middle">
                            <thead class="table-dark">
                                <tr>
                                    <th>Tanggal</th>
                                    <th>Nama (NIM)</th>
                                    <th>Jenis</th>
                                    <th>Keterangan</th>
                                    <th>Bukti</th>
                                    <th>Status</th>
                                    @if(in_array(Auth::user()->role, ['admin', 'dosen']))
                                    <th>Aksi</th>
                                    @endif
                                </tr>
                            </thead>
                            <tbody>
                                @forelse($data_izin as $izin)
                                <tr>
                                    <td>{{ \Carbon\Carbon::parse($izin->tanggal)->format('d/m/Y') }}</td>
                                    <td>
                                        <span class="fw-bold">{{ $izin->Nama }}</span><br>
                                        <small>{{ $izin->NIM }}</small>
                                    </td>
                                    <td>
                                        <span class="badge {{ $izin->jenis_izin == 'Sakit' ? 'bg-warning' : 'bg-info' }}">
                                            {{ $izin->jenis_izin }}
                                        </span>
                                    </td>
                                    <td>{{ $izin->keterangan }}</td>
                                    <td>
                                        @if($izin->bukti_dokumen)
                                            <a href="{{ asset('storage/'.$izin->bukti_dokumen) }}" target="_blank" class="btn btn-sm btn-outline-secondary">
                                                <i class="fas fa-eye"></i> Lihat
                                            </a>
                                        @else
                                            -
                                        @endif
                                    </td>
                                    <td>
                                        @if($izin->status_approval == 'Pending')
                                            <span class="badge bg-secondary">Pending</span>
                                        @elseif($izin->status_approval == 'Disetujui')
                                            <span class="badge bg-success">Disetujui</span>
                                        @else
                                            <span class="badge bg-danger">Ditolak</span>
                                        @endif
                                    </td>
                                    
                                    @if(in_array(Auth::user()->role, ['admin', 'dosen']))
                                    <td>
                                        @if($izin->status_approval == 'Pending')
                                            <form action="{{ route('izin.update', $izin->id) }}" method="POST" class="d-inline">
                                                @csrf
                                                <input type="hidden" name="status" value="Disetujui">
                                                <button class="btn btn-sm btn-success" onclick="return confirm('Setujui izin ini?')"><i class="fas fa-check"></i></button>
                                            </form>
                                            <form action="{{ route('izin.update', $izin->id) }}" method="POST" class="d-inline">
                                                @csrf
                                                <input type="hidden" name="status" value="Ditolak">
                                                <button class="btn btn-sm btn-danger" onclick="return confirm('Tolak izin ini?')"><i class="fas fa-times"></i></button>
                                            </form>
                                        @else
                                            <i class="fas fa-lock text-muted"></i> Selesai
                                        @endif
                                    </td>
                                    @endif
                                </tr>
                                @empty
                                <tr>
                                    <td colspan="7" class="text-center py-3">Belum ada data pengajuan.</td>
                                </tr>
                                @endforelse
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>

</body>
</html>