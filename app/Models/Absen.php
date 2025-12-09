<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Absen extends Model
{
    use HasFactory;

    protected $table = 'absen'; // Memberitahu Laravel nama tabelnya
    public $timestamps = false; // Karena di SQL anda tidak ada created_at/updated_at standar Laravel
    
    // Jika ingin mass assignment (simpan data langsung banyak)
    protected $guarded = ['id'];

    // Relasi ke User (Opsional, tapi bagus untuk join data)
    public function user()
    {
        return $this->belongsTo(User::class, 'NIM', 'NIM');
    }
}