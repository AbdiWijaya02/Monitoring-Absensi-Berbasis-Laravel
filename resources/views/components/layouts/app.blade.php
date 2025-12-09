<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIoT Monitoring System</title>
    <link rel="icon" href="{{ asset('images/logobrail.jpg') }}" type="image/jpg">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    @livewireStyles
</head>
<body class="bg-light">

    <nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4 shadow-sm">
        <div class="container">
        <a class="navbar-brand fw-bold d-flex align-items-center" href="#">
            <img src="{{ asset('images/logopolibatam.png') }}" alt="Logo Poli" height="40" class="me-2 bg-white rounded-circle p-1">
            
            <img src="{{ asset('images/logobrail.jpg') }}" alt="Logo BRAIL" height="40" class="me-2 rounded-circle">
            
            <span>AIoT Monitoring</span>
        </a>            
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>

            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto mb-2 mb-lg-0">
                    <li class="nav-item">
                        <a class="nav-link" href="{{ route('monitoring.index') }}">Dashboard</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ route('izin.index') }}">Pengajuan Izin</a>
                    </li>
                </ul>

                <div class="d-flex text-white align-items-center">
                    <div class="me-3 text-end d-none d-lg-block">
                        <small class="d-block text-secondary" style="font-size: 0.7rem;">Login Sebagai</small>
                        <span class="fw-bold">{{ Auth::user()->Nama ?? 'Guest' }}</span> 
                        <span class="badge bg-info text-dark ms-1">{{ Auth::user()->role ?? '-' }}</span>
                    </div>
                    <form action="{{ route('logout') }}" method="POST">
                        @csrf
                        <button class="btn btn-sm btn-danger"><i class="fas fa-sign-out-alt"></i> Logout</button>
                    </form>
                </div>
            </div>
        </div>
    </nav>

    {{ $slot }}

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    @livewireScripts
</body>
</html>