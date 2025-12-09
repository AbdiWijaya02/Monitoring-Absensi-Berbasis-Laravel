<!DOCTYPE html>
<html>
<head>
    <title>Login Absensi</title>
    <link rel="icon" href="{{ asset('images/logobrail.jpg') }}" type="image/jpg">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light d-flex align-items-center justify-content-center" style="height: 100vh;">
    
    <div class="card shadow p-4" style="width: 400px;">
        <div class="text-center mb-4">
            <img src="{{ asset('images/logopolibatam.png') }}" width="80" class="me-3">
            <img src="{{ asset('images/logobrail.jpg') }}" width="80" class="rounded-circle">
        </div>

        <h3 class="text-center mb-4">Login</h3>
        @if (session('success'))
            <div class="alert alert-success alert-dismissible fade show" role="alert">
                {{ session('success') }}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        @endif

        @if ($errors->any())
            <div class="alert alert-danger">
                <ul class="mb-0">
                    @foreach ($errors->all() as $error)
                        <li>{{ $error }}</li>
                    @endforeach
                </ul>
            </div>
        @endif

        <form action="{{ route('login.post') }}" method="POST">
            @csrf
            <div class="mb-3">
                <label class="form-label">NIM</label>
                <input type="NIM" name="NIM" class="form-control" placeholder="Masukkan NIM" required>
            </div>
            <div class="mb-3">
                <label class="form-label">Password</label>
                <input type="password" name="password" class="form-control" placeholder="Masukkan Password" required>
            </div>
            
            <button type="submit" class="btn btn-primary w-100 mb-3">Masuk</button>
            
            <div class="text-center">
                Belum punya akun? <a href="{{ route('register') }}">Daftar disini</a>
            </div>
        </form>
    </div>

</body>
</html>