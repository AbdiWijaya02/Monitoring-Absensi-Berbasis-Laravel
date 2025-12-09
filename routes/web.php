<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\LoginController;
use App\Http\Controllers\RegisterController;
use App\Http\Controllers\IzinController;
use App\Livewire\MonitoringDashboard; // Import Livewire

// Route Tamu
Route::middleware('guest')->group(function () {
    Route::get('/login', [LoginController::class, 'index'])->name('login');
    Route::post('/login', [LoginController::class, 'authenticate'])->name('login.post');
    Route::get('/register', [RegisterController::class, 'index'])->name('register');
    Route::post('/register', [RegisterController::class, 'store'])->name('register.store');
});

// Route User Login
Route::middleware('auth')->group(function () {
    
    // Ganti route lama dengan Livewire Component
    Route::get('/monitoring', MonitoringDashboard::class)->name('monitoring.index');

    // Route Izin
    Route::get('/izin', [IzinController::class, 'index'])->name('izin.index');
    Route::post('/izin', [IzinController::class, 'store'])->name('izin.store');
    Route::post('/izin/update/{id}', [IzinController::class, 'updateStatus'])->name('izin.update');

    Route::post('/logout', [LoginController::class, 'logout'])->name('logout');

    Route::get('/', function () {
        return redirect('/monitoring');
    });
});