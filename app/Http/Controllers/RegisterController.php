<?php

namespace App\Http\Controllers;

use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;

class RegisterController extends Controller
{
    // 1. Menampilkan Form Register
    public function index()
    {
        return view('auth.register');
    }

    // 2. Memproses Data Register
    public function store(Request $request)
    {
        // 1. Update Validasi
        $request->validate([
            'nama' => 'required|max:255',
            'nim' => 'required|numeric|unique:user,NIM',
            'email' => 'required|email|unique:user,email',
            'pbl' => 'required|string|max:100',
            'gender' => 'required|string|max:100', // Validasi maks 6 karakter
            'angkatan' => 'required|numeric',    // Validasi angka
            'password' => 'required|min:5|confirmed',
        ]);

        // 2. Update Simpan Database
        User::create([
            'userid' => rand(1, 1000),
            'Nama' => $request->nama,
            'NIM' => $request->nim,
            'email' => $request->email,
            'PBL' => $request->pbl,
            
            // Tambahkan 2 baris ini
            'gender' => $request->gender,
            'Angkatan' => $request->angkatan, // Sesuai nama kolom di DB (Huruf A Besar)

            'Password' => Hash::make($request->password),
            'role' => 'user',
        ]);

        return redirect()->route('login')->with('success', 'Registrasi berhasil! Silakan login.');
    }
}