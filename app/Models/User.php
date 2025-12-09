<?php

namespace App\Models;

use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;

class User extends Authenticatable
{
    use Notifiable;

    protected $table = 'user';
    protected $primaryKey = 'id';

    // --- FIX 1: Matikan Timestamps ---
    // Agar Laravel tidak mencari kolom 'updated_at' & 'created_at'
    public $timestamps = false;

    protected $fillable = [
        'userid', 'Nama', 'NIM', 'email', 'Password', 'role', 'PBL', 'gender', 'Angkatan'
    ];

    protected $hidden = [
        'Password', 'remember_token',
    ];

    // --- FIX 2: Definisikan Nama Kolom Password ---
    // Memberi tahu Laravel bahwa kolom password kita bernama 'Password' (Huruf Besar P)
    // Ini penting agar fitur update password otomatis tidak error 'Column not found: password'
    public function getAuthPasswordName()
    {
        return 'Password';
    }

    // Fungsi ini tetap dibutuhkan untuk mengambil isi password saat login
    public function getAuthPassword()
    {
        return $this->Password;
    }
}