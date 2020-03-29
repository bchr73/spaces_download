#!/usr/bin/env python3
from download import DownloadManager
from contract import ContractFactory

if __name__ == '__main__':

    filenames = [
            'The.Mandalorian.S01E01.INTERNAL.1080p.WEB.H264-DEFLATE.mkv',
            'The.Mandalorian.S01E02.1080p.WEBRip.DDP5.1.x264-CUSTOM.mkv',
            'The.Mandalorian.S01E03.1080p.WEB.H264-PETRiFiED.mkv',
            'The.Mandalorian.S01E04.1080p.WEBRiP.x264-PETRiFiED.mkv',
            'The.Mandalorian.S01E05.1080p.WEBRiP.x264-PETRiFiED.mkv',
            'The.Mandalorian.S01E06.REPACK.1080p.WEBRiP.x264-PETRiFiED.mkv',
            'The.Mandalorian.S01E07.1080p.WEBRiP.x264-PETRiFiED.mkv',
            'The.Mandalorian.S01E08.1080p.WEBRiP.x264-PETRiFiED.mkv'
        ]
    sam_cham = 'samurai_champloo_ep1.mkv'

    dm = DownloadManager()
    cf = ContractFactory('karim-storage')

    contract = cf.new(sam_cham, sam_cham)

    dm.submit(contract)
    dm.start()

