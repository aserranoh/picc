'''Package that implements the functionalities of picc.

Copyright 2016 Antonio Serrano Hernandez

This file is part of picc.

picc is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

picc is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with picc; see the file COPYING.  If not, see
<http://www.gnu.org/licenses/>.
'''

__author__ = 'Antonio Serrano Hernandez'
__copyright__ = 'Copyright (C) 2016 Antonio Serrano Hernandez'
__version__ = '0.2.1'
__license__ = 'GPL'
__maintainer__ = 'Antonio Serrano Hernandez'
__email__ = 'toni.serranoh@gmail.com'
__status__ = 'Development'
__homepage__ = 'https://github.com/aserranoh/picc'

VERSION_STRING = '''\
%(prog)s {version}
{copyright}
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.\
'''.format(version=__version__, copyright=__copyright__)

HELP_EPILOG = '''\
Report bugs to: {email}
picc home page: {homepage}
'''.format(email=__email__, homepage=__homepage__)

