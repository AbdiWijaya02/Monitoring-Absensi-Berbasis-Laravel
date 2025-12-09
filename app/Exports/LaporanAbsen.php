<?php

namespace App\Exports;

use App\Models\Absen;
use Maatwebsite\Excel\Concerns\FromCollection;
use Maatwebsite\Excel\Concerns\WithHeadings;
use Maatwebsite\Excel\Concerns\ShouldAutoSize;

class LaporanAbsen implements FromCollection, WithHeadings, ShouldAutoSize
{
    protected $startDate;
    protected $endDate;

    public function __construct($startDate, $endDate)
    {
        $this->startDate = $startDate;
        $this->endDate = $endDate;
    }

    public function collection()
    {
        return Absen::whereBetween('tanggal', [$this->startDate, $this->endDate])
                    ->orderBy('tanggal', 'asc')
                    ->select('tanggal', 'NIM', 'Nama', 'PBL', 'status_kehadiran', 'status_masuk', 'durasi_kerja')
                    ->get();
    }

    public function headings(): array
    {
        return ["Tanggal", "NIM", "Nama", "PBL", "Status Kehadiran", "Keterangan", "Durasi (Jam)"];
    }
}