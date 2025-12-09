<?php

namespace App\Livewire;

use Livewire\Component;
use Livewire\WithPagination;
use App\Models\Absen;
use App\Models\User;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\DB; // <--- JANGAN LUPA INI
use Carbon\Carbon;
use Maatwebsite\Excel\Facades\Excel;
use App\Exports\LaporanAbsen;
use Barryvdh\DomPDF\Facade\Pdf;

class MonitoringDashboard extends Component
{
    use WithPagination;

    public $startDate;
    public $endDate;
    public $filterPbl = '';
    public $filterAngkatan = '';
    protected $paginationTheme = 'bootstrap';
    public $pblOptions = [];
    public $angkatanOptions = [];

    public function mount()
    {
        $this->startDate = Carbon::today()->toDateString();
        $this->endDate = Carbon::today()->toDateString();
        
        $this->pblOptions = User::select('PBL')->distinct()->whereNotNull('PBL')->pluck('PBL');
        $this->angkatanOptions = User::select('Angkatan')->distinct()->whereNotNull('Angkatan')->orderBy('Angkatan', 'desc')->pluck('Angkatan');
    }

    public function render()
    {
        $user = Auth::user();
        $query = Absen::query()->with('user');

        // 1. Filter Role
        if (!in_array($user->role, ['admin', 'dosen'])) {
            $query->where('NIM', $user->NIM);
        }

        // 2. Filter Tanggal
        $query->whereBetween('tanggal', [$this->startDate, $this->endDate]);

        // 3. Filter Dropdown
        if ($this->filterPbl) {
            $query->where('PBL', $this->filterPbl);
        }
        if ($this->filterAngkatan) {
            $query->whereHas('user', function($q) {
                $q->where('Angkatan', $this->filterAngkatan);
            });
        }

        // 4. Statistik Global (Pie Chart)
        $statQuery = $query->clone();
        $hadirCount = $statQuery->clone()->where('status_kehadiran', 'Hadir')->count();
        $tidakHadirCount = $statQuery->clone()->where('status_kehadiran', '!=', 'Hadir')->count();

        // --- TAMBAHAN BARU: DATA GRAFIK BATANG (PER PBL) ---
        // Menghitung jumlah 'Hadir' dikelompokkan berdasarkan nama PBL
        $pblStats = $statQuery->clone()
            ->where('status_kehadiran', 'Hadir')
            ->select('PBL', DB::raw('count(*) as total'))
            ->groupBy('PBL')
            ->orderBy('total', 'desc')
            ->limit(10) // Ambil Top 10 PBL agar grafik tidak kepenuhan
            ->get();

        $pblLabels = $pblStats->pluck('PBL'); // Nama Tim (Sumbu X)
        $pblData   = $pblStats->pluck('total'); // Jumlah Hadir (Sumbu Y)
        // ----------------------------------------------------

        $totalData = $hadirCount + $tidakHadirCount;
        $persentase = ($totalData > 0) ? round(($hadirCount / $totalData) * 100) : 0;

        // 5. Kirim Event Update Chart (Pie + Bar)
        $this->dispatch('update-chart', [
            'hadir' => $hadirCount, 
            'tidakHadir' => $tidakHadirCount,
            'pblLabels' => $pblLabels, // Kirim label bar chart
            'pblData' => $pblData      // Kirim data bar chart
        ]);

        $data_absen = $query->clone()
                            ->orderBy('tanggal', 'desc')
                            ->orderBy('absen_hadir', 'desc')
                            ->paginate(10);

        return view('livewire.monitoring-dashboard', [
            'data_absen' => $data_absen,
            'hadirCount' => $hadirCount,
            'tidakHadirCount' => $tidakHadirCount,
            'persentase' => $persentase
        ]);
    }

    public function exportExcel()
    {
        return Excel::download(new LaporanAbsen($this->startDate, $this->endDate), 'Laporan_Absensi.xlsx');
    }

    public function downloadPDF()
    {
        $query = Absen::query()->with('user');
        
        if (!in_array(Auth::user()->role, ['admin', 'dosen'])) {
            $query->where('NIM', Auth::user()->NIM);
        }

        $query->whereBetween('tanggal', [$this->startDate, $this->endDate]);

        if ($this->filterPbl) $query->where('PBL', $this->filterPbl);
        if ($this->filterAngkatan) {
            $query->whereHas('user', function($q) {
                $q->where('Angkatan', $this->filterAngkatan);
            });
        }

        $data_absen = $query->orderBy('tanggal', 'asc')->get();

        $pdf = Pdf::loadView('monitoring.pdf_report', [
            'data_absen' => $data_absen,
            'startDate' => $this->startDate,
            'endDate' => $this->endDate,
            'userCetak' => Auth::user()->Nama
        ]);

        $pdf->setPaper('a4', 'landscape');

        return response()->streamDownload(function () use ($pdf) {
            echo $pdf->output();
        }, 'Laporan_Resmi.pdf');
    }
}