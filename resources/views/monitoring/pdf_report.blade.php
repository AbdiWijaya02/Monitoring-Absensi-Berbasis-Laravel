<!DOCTYPE html>
<html>
<head>
    <title>Laporan Absensi</title>
    <style>
        body { font-family: sans-serif; font-size: 12px; }
        .header { text-align: center; margin-bottom: 20px; }
        .header h2, .header h4 { margin: 0; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        table, th, td { border: 1px solid black; }
        th, td { padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .ttd { width: 100%; margin-top: 50px; }
        .ttd-box { float: right; width: 250px; text-align: center; }
    </style>
</head>
<body>
    <div class="header">
        <h2>POLITEKNIK NEGERI BATAM</h2>
        <h4>LAPORAN REKAPITULASI KEHADIRAN</h4>
        <small>Jl. Ahmad Yani, Teluk Tering, Batam Kota</small>
        <hr>
    </div>

    <div style="margin-bottom: 15px;">
        <strong>Periode:</strong> {{ \Carbon\Carbon::parse($startDate)->format('d F Y') }} s/d {{ \Carbon\Carbon::parse($endDate)->format('d F Y') }} <br>
        <strong>Dicetak Oleh:</strong> {{ $userCetak }}
    </div>

    <table>
        <thead>
            <tr>
                <th style="width: 5%">No</th>
                <th style="width: 15%">Tanggal</th>
                <th style="width: 15%">NIM</th>
                <th style="width: 25%">Nama</th>
                <th style="width: 10%">PBL</th>
                <th style="width: 10%">Masuk</th>
                <th style="width: 10%">Pulang</th>
                <th style="width: 10%">Status</th>
            </tr>
        </thead>
        <tbody>
            @forelse($data_absen as $index => $absen)
            <tr>
                <td style="text-align: center">{{ $index + 1 }}</td>
                <td>{{ \Carbon\Carbon::parse($absen->tanggal)->format('d/m/Y') }}</td>
                <td>{{ $absen->NIM }}</td>
                <td>{{ $absen->Nama }}</td>
                <td>{{ $absen->PBL }}</td>
                <td>{{ $absen->absen_hadir ? \Carbon\Carbon::parse($absen->absen_hadir)->format('H:i') : '-' }}</td>
                <td>{{ $absen->absen_pulang ? \Carbon\Carbon::parse($absen->absen_pulang)->format('H:i') : '-' }}</td>
                <td>{{ $absen->status_kehadiran }}</td>
            </tr>
            @empty
            <tr><td colspan="8" style="text-align: center">Data Kosong</td></tr>
            @endforelse
        </tbody>
    </table>

    <div class="ttd">
        <div class="ttd-box">
            <p>Batam, {{ \Carbon\Carbon::now()->format('d F Y') }}</p>
            <p>Mengetahui,</p>
            <br><br><br>
            <p><strong>( _______________________ )</strong></p>
            <p>Kaprodi / Dosen Wali</p>
        </div>
    </div>
</body>
</html>