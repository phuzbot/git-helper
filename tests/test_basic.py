from .context import githelper
import unittest


class BasicTest(unittest.TestCase):

    def passing_test(self):
        self.assertNotEquals(githelper.get_head_hash(), 'hello world')


if __name__ == '__main__':
    unittest.main()
