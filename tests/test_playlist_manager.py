import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import playlist_manager as manager


class PlaylistTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    @patch('playlist_manager.today', return_value=date(2026, 11, 26))
    @patch('playlist_manager.download_txt', return_value='央视,#genre#\nCCTV1,http://example.com/live\nCCTV1,http://example.com/backup\n')
    def test_generate(self, download, _today):
        target = manager.generate(self.root, 'beijing', '移动', 'user_1', '2026-12-31')
        self.assertEqual(target.relative_to(self.root).as_posix(),
                         'beijing-mobile-user_1-2026-12-31/playlist.m3u')
        self.assertEqual(target.read_text().count('#EXTINF:'), 2)
        self.assertIn('group-title="央视"', target.read_text())
        download.assert_called_once_with(manager.BASE_URL + '/beijing/mobile.txt')

    @patch('playlist_manager.today', return_value=date(2026, 11, 26))
    @patch('playlist_manager.download_txt')
    def test_invalid_input_never_downloads(self, download, _today):
        for province, operator, username, expires in [
            ('../foo', 'mobile', 'user', '2026-12-31'),
            ('beijing', 'bad', 'user', '2026-12-31'),
            ('beijing', 'mobile', '../user', '2026-12-31'),
            ('beijing', 'mobile', 'user', '2026-11-26'),
            ('beijing', 'mobile', 'user', '2026-02-30'),
        ]:
            with self.subTest(province=province, username=username, expires=expires):
                with self.assertRaises(ValueError):
                    manager.generate(self.root, province, operator, username, expires)
        download.assert_not_called()

    @patch('playlist_manager.today', return_value=date(2026, 11, 26))
    @patch('playlist_manager.download_txt', return_value='no channels')
    def test_conversion_failure_preserves_existing(self, _download, _today):
        directory = self.root / 'shanxi-mobile-user-2026-12-31'
        directory.mkdir()
        target = directory / 'playlist.m3u'
        target.write_text('previous playlist')
        with self.assertRaises(RuntimeError):
            manager.generate(self.root, 'shanxi', 'mobile', 'user', '2026-12-31')
        self.assertEqual(target.read_text(), 'previous playlist')

    def test_cleanup_only_expired_matching_directories(self):
        names = ['beijing-mobile-user-2026-11-25', 'shanxi-unicom-user_1-2026-11-26',
                 'beijing-telecom-user-2026-11-27', 'other-2026-11-25',
                 'beijing-mobile-user-2026-02-30']
        for name in names:
            directory = self.root / name
            directory.mkdir()
            (directory / 'playlist.m3u').write_text('test')
        (self.root / 'shanxi_mobile.m3u').write_text('legacy')
        (self.root / 'beijing-mobile-link-2026-11-25').symlink_to(self.root / names[2], target_is_directory=True)
        self.assertEqual(manager.cleanup(self.root, date(2026, 11, 26)), sorted(names[:2]))
        for name in names[2:]:
            self.assertTrue((self.root / name).exists())
        self.assertTrue((self.root / 'shanxi_mobile.m3u').exists())
        self.assertEqual(manager.cleanup(self.root, date(2026, 11, 26)), [])


if __name__ == '__main__':
    unittest.main()
