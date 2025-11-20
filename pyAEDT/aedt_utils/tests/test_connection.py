"""
pytest를 사용한 aedt_utils 테스트

실행 방법:
    pytest tests/test_connection.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from aedt_utils import connection


class TestGetAedtProcessesDetailed:
    """getAedtProcessesDetailed 함수 테스트"""
    
    @patch('aedt_utils.connection.psutil.process_iter')
    def test_no_processes(self, mock_process_iter):
        """AEDT 프로세스가 없는 경우"""
        mock_process_iter.return_value = []
        
        result = connection.getAedtProcessesDetailed()
        
        assert result == []
    
    @patch('aedt_utils.connection.psutil.process_iter')
    def test_with_aedt_process(self, mock_process_iter):
        """AEDT 프로세스가 있는 경우"""
        # Mock process
        mock_proc = Mock()
        mock_proc.info = {
            'pid': 1234,
            'name': 'ansysedt.exe',
            'cmdline': ['ansysedt.exe'],
            'create_time': 1234567890.0
        }
        
        mock_proc.connections.return_value = []
        
        mock_process_iter.return_value = [mock_proc]
        
        result = connection.getAedtProcessesDetailed()
        
        assert len(result) == 1
        assert result[0]['pid'] == 1234
        assert result[0]['name'] == 'ansysedt.exe'


class TestTryConnectToExistingDesktop:
    """tryConnectToExistingDesktop 함수 테스트"""
    
    @patch('aedt_utils.connection.Desktop')
    def test_successful_connection(self, mock_desktop):
        """연결 성공 케이스"""
        mock_desktop_instance = Mock()
        mock_desktop.return_value = mock_desktop_instance
        
        result = connection.tryConnectToExistingDesktop()
        
        assert result == mock_desktop_instance
        mock_desktop.assert_called_once()
    
    @patch('aedt_utils.connection.Desktop')
    def test_connection_failure(self, mock_desktop):
        """연결 실패 케이스"""
        mock_desktop.side_effect = Exception("Connection failed")
        
        result = connection.tryConnectToExistingDesktop()
        
        assert result is None


class TestTryConnectWithPorts:
    """tryConnectWithPorts 함수 테스트"""
    
    @patch('aedt_utils.connection.Desktop')
    def test_successful_connection_first_port(self, mock_desktop):
        """첫 번째 포트로 연결 성공"""
        mock_desktop_instance = Mock()
        mock_desktop.return_value = mock_desktop_instance
        
        result = connection.tryConnectWithPorts([56800, 56801])
        
        assert result == mock_desktop_instance
    
    @patch('aedt_utils.connection.Desktop')
    def test_all_ports_fail(self, mock_desktop):
        """모든 포트 연결 실패"""
        mock_desktop.side_effect = Exception("Connection failed")
        
        result = connection.tryConnectWithPorts([56800, 56801])
        
        assert result is None


class TestGetDesktopConnection:
    """getDesktopConnection 함수 테스트"""
    
    @patch('aedt_utils.connection.tryConnectToExistingDesktop')
    def test_connect_to_existing(self, mock_try_connect):
        """기존 Desktop 연결 성공"""
        mock_desktop = Mock()
        mock_try_connect.return_value = mock_desktop
        
        result = connection.getDesktopConnection()
        
        assert result == mock_desktop
    
    @patch('aedt_utils.connection.Desktop')
    @patch('aedt_utils.connection.tryConnectWithPorts')
    @patch('aedt_utils.connection.getAedtProcessesDetailed')
    @patch('aedt_utils.connection.tryConnectToExistingDesktop')
    def test_fallback_to_new_session(
        self, 
        mock_try_existing,
        mock_get_processes,
        mock_try_ports,
        mock_desktop
    ):
        """새 세션 생성으로 fallback"""
        # 기존 연결 실패
        mock_try_existing.return_value = None
        
        # 프로세스 없음
        mock_get_processes.return_value = []
        
        # 포트 연결 실패
        mock_try_ports.return_value = None
        
        # 새 세션 생성 성공
        mock_desktop_instance = Mock()
        mock_desktop.return_value = mock_desktop_instance
        
        result = connection.getDesktopConnection()
        
        assert result == mock_desktop_instance


class TestCheckCurrentDesktopStatus:
    """checkCurrentDesktopStatus 함수 테스트"""
    
    def test_none_desktop(self, capsys):
        """Desktop이 None인 경우"""
        connection.checkCurrentDesktopStatus(None)
        
        captured = capsys.readouterr()
        assert "Desktop 객체가 없습니다" in captured.out
    
    def test_with_valid_desktop(self, capsys):
        """유효한 Desktop인 경우"""
        mock_desktop = Mock()
        mock_desktop.aedt_version_id = "2025.2"
        mock_desktop.aedt_process_id = 1234
        mock_desktop.project_list.return_value = ["Project1"]
        
        mock_proj = Mock()
        mock_proj.GetName.return_value = "Project1"
        mock_desktop.active_project.return_value = mock_proj
        
        connection.checkCurrentDesktopStatus(mock_desktop)
        
        captured = capsys.readouterr()
        assert "Desktop 상태" in captured.out
        assert "2025.2" in captured.out


class TestSmartAedtConnector:
    """smartAedtConnector 함수 테스트"""
    
    @patch('aedt_utils.connection.checkCurrentDesktopStatus')
    @patch('aedt_utils.connection.getDesktopConnection')
    def test_successful_connection(self, mock_get_desktop, mock_check_status):
        """연결 성공"""
        mock_desktop = Mock()
        mock_get_desktop.return_value = mock_desktop
        
        result = connection.smartAedtConnector()
        
        assert result == mock_desktop
        mock_check_status.assert_called_once_with(mock_desktop)
    
    @patch('aedt_utils.connection.getDesktopConnection')
    def test_connection_failure(self, mock_get_desktop):
        """연결 실패"""
        mock_get_desktop.return_value = None
        
        result = connection.smartAedtConnector()
        
        assert result is None


class TestQuickConnect:
    """quickConnect 함수 테스트"""
    
    @patch('aedt_utils.connection.tryConnectToExistingDesktop')
    def test_quick_connect(self, mock_try_connect):
        """빠른 연결 테스트"""
        mock_desktop = Mock()
        mock_try_connect.return_value = mock_desktop
        
        result = connection.quickConnect()
        
        assert result == mock_desktop


class TestForceNewSession:
    """forceNewSession 함수 테스트"""
    
    @patch('aedt_utils.connection.Desktop')
    def test_force_new_session_success(self, mock_desktop):
        """새 세션 생성 성공"""
        mock_desktop_instance = Mock()
        mock_desktop.return_value = mock_desktop_instance
        
        result = connection.forceNewSession()
        
        assert result == mock_desktop_instance
        mock_desktop.assert_called_once()
    
    @patch('aedt_utils.connection.Desktop')
    def test_force_new_session_failure(self, mock_desktop):
        """새 세션 생성 실패"""
        mock_desktop.side_effect = Exception("Creation failed")
        
        result = connection.forceNewSession()
        
        assert result is None
