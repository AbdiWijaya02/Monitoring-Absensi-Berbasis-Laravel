<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;

class LoginController extends Controller
{
    public function index()
    {
        return view('auth.login');
    }

    public function authenticate(Request $request)
    {
        // Ubah validasi jadi 'NIM'
        $request->validate([
            'NIM' => ['required'],
            'password' => ['required'],
        ]);

        // Auth::attempt pakai array parameter. Kiri: nama kolom di DB, Kanan: input dari form
        if (Auth::attempt(['NIM' => $request->NIM, 'password' => $request->password])) {
            $request->session()->regenerate();
            return redirect()->intended('monitoring');
        }

        return back()->withErrors([
            'NIM' => 'NIM atau password salah.',
        ]);
    }

    public function logout(Request $request)
    {
        Auth::logout();
 
        $request->session()->invalidate();
     
        $request->session()->regenerateToken();
     
        return redirect('/login');
    }
}