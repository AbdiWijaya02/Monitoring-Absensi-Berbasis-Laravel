<!DOCTYPE html>
<html>
<head>
    <title>Daftar Akun Baru</title>
    <link rel="icon" href="{{ asset('images/logobrail.jpg') }}" type="image/jpg">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light d-flex align-items-center justify-content-center" style="min-height: 100vh;">

    <div class="card shadow p-4 my-5" style="width: 500px;">
        <h3 class="text-center mb-4">Register Akun</h3>

        @if ($errors->any())
            <div class="alert alert-danger">
                <ul class="mb-0">
                    @foreach ($errors->all() as $error)
                        <li>{{ $error }}</li>
                    @endforeach
                </ul>
            </div>
        @endif

        <form action="{{ route('register.store') }}" method="POST">
            @csrf
            
            <div class="mb-3">
                <label class="form-label">Nama Lengkap</label>
                <input type="text" name="nama" class="form-control" value="{{ old('nama') }}" required>
            </div>

            <div class="mb-3">
                <label class="form-label">NIM</label>
                <input type="number" name="nim" class="form-control" value="{{ old('nim') }}" required>
            </div>

            <div class="mb-3">
                <label class="form-label">Email</label>
                <input type="email" name="email" class="form-control" value="{{ old('email') }}" required>
            </div>

            <div class="mb-3">
                <label class="form-label">Nama Tim PBL</label>
                <input type="text" name="pbl" class="form-control" value="{{ old('pbl') }}" placeholder="Contoh: AIOT, MALAS" required>
            </div>

            <div class="row">
                <div class="col-md-6 mb-3">
                    <label class="form-label">Jenis Kelamin</label>
                    <select name="gender" class="form-select" required>
                        <option value="" disabled selected>Pilih...</option>
                        <option value="Laki-L" {{ old('gender') == 'Laki-L' ? 'selected' : '' }}>Laki-laki</option>
                        <option value="Wanita" {{ old('gender') == 'Wanita' ? 'selected' : '' }}>Perempuan</option> 
                    </select>
                </div>
                <div class="col-md-6 mb-3">
                    <label class="form-label">Angkatan</label>
                    <select name="angkatan" class="form-select" required>
                        <option value="" disabled selected>Pilih Tahun...</option>
                        
                        @for ($tahun = 2020; $tahun <= 2025; $tahun++)
                            <option value="{{ $tahun }}" {{ old('angkatan') == $tahun ? 'selected' : '' }}>
                                {{ $tahun }}
                            </option>
                        @endfor
                        
                    </select>
                </div>
            </div>

            <div class="mb-3">
                <label class="form-label">Password</label>
                <input type="password" name="password" class="form-control" required>
            </div>

            <div class="mb-3">
                <label class="form-label">Konfirmasi Password</label>
                <input type="password" name="password_confirmation" class="form-control" required>
                <small class="text-muted">Ketik ulang password Anda.</small>
            </div>

            <button type="submit" class="btn btn-success w-100 mb-3">Daftar Sekarang</button>
            
            <div class="text-center">
                Sudah punya akun? <a href="{{ route('login') }}">Login disini</a>
            </div>
        </form>
    </div>

</body>
</html>