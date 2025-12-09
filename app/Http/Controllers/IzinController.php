<?php

namespace App\Http\Controllers;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use App\Models\PengajuanIzin;
use App\Models\Absen;
use Illuminate\Support\Facades\Auth;
use Carbon\Carbon;

class IzinController extends Controller
{
    // --- HALAMAN USER: Form Pengajuan ---
    public function index()
    {
        $user = Auth::user();
        
        // Admin melihat semua request, User hanya melihat miliknya
        if (in_array($user->role, ['admin', 'dosen'])) {
            $data_izin = PengajuanIzin::orderBy('created_at', 'desc')->get();
        } else {
            $data_izin = PengajuanIzin::where('NIM', $user->NIM)->orderBy('created_at', 'desc')->get();
        }

        return view('izin.index', compact('data_izin'));
    }

    // --- PROSES USER: Simpan Pengajuan ---
    public function store(Request $request)
    {
        $request->validate([
            'tanggal' => 'required|date',
            'jenis_izin' => 'required',
            'keterangan' => 'required',
            'bukti_dokumen' => 'nullable|image|mimes:jpeg,png,jpg|max:2048', // Max 2MB
        ]);

        $user = Auth::user();

        // Upload Bukti (Surat Dokter dll)
        $path = null;
        if ($request->hasFile('bukti_dokumen')) {
            $path = $request->file('bukti_dokumen')->store('dokumen_izin', 'public');
        }

        PengajuanIzin::create([
            'NIM' => $user->NIM,
            'Nama' => $user->Nama,
            'PBL' => $user->PBL,
            'tanggal' => $request->tanggal,
            'jenis_izin' => $request->jenis_izin,
            'keterangan' => $request->keterangan,
            'bukti_dokumen' => $path,
            'status_approval' => 'Pending'
        ]);

        return redirect()->back()->with('success', 'Pengajuan berhasil dikirim. Menunggu persetujuan Admin.');
    }

    // --- PROSES ADMIN: Approve/Reject ---
    public function updateStatus(Request $request, $id)
    {
        // Validasi Role
        if (!in_array(Auth::user()->role, ['admin', 'dosen'])) {
            abort(403);
        }

        $pengajuan = PengajuanIzin::findOrFail($id);
        $statusBaru = $request->status; // Disetujui atau Ditolak

        $pengajuan->update(['status_approval' => $statusBaru]);

        // LOGIKA PENTING: Jika Disetujui, Masukkan ke Tabel Absen
        if ($statusBaru == 'Disetujui') {
            // Cek dulu apakah sudah ada data di tanggal itu (biar ga duplikat)
            $cekAbsen = Absen::where('NIM', $pengajuan->NIM)
                             ->whereDate('tanggal', $pengajuan->tanggal)
                             ->first();

            if (!$cekAbsen) {
                Absen::create([
                    'NIM' => $pengajuan->NIM,
                    'Nama' => $pengajuan->Nama,
                    'PBL' => $pengajuan->PBL,
                    'tanggal' => $pengajuan->tanggal,
                    'status_kehadiran' => $pengajuan->jenis_izin, // Sakit atau Izin
                    'status_masuk' => 'Approved',
                    'durasi_kerja' => 0 // Sakit tidak ada jam kerja
                ]);
            } else {
                // Jika sudah ada (misal tertulis Alpha), update jadi Sakit/Izin
                $cekAbsen->update([
                    'status_kehadiran' => $pengajuan->jenis_izin,
                    'status_masuk' => 'Approved'
                ]);
            }
        }

        return redirect()->back()->with('success', 'Status pengajuan berhasil diperbarui.');
    }
}