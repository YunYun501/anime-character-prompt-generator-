"""
Tests for the FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient
import json
from pathlib import Path

# Import the FastAPI app
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from web.server import app


client = TestClient(app)


class TestSlotsAPI:
    """Test slots-related endpoints."""
    
    def test_get_slots(self):
        """Test GET /api/slots endpoint."""
        response = client.get("/api/slots")
        assert response.status_code == 200
        
        data = response.json()
        assert "slots" in data
        assert "sections" in data
        
        # Check slot structure
        slots = data["slots"]
        assert "hair_style" in slots
        assert "upper_body" in slots
        assert "background" in slots
        
        # Check slot properties
        hair_slot = slots["hair_style"]
        assert "category" in hair_slot
        assert "has_color" in hair_slot
        assert "options" in hair_slot
        
    def test_randomize_all(self):
        """Test POST /api/randomize-all endpoint."""
        response = client.post(
            "/api/randomize-all",
            json={
                "locked": {},
                "palette_enabled": True,
                "palette_id": None,
                "full_body_mode": False,
                "upper_body_mode": False
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        
        results = data["results"]
        assert isinstance(results, dict)
        
        # Check that we got some randomized slots
        assert len(results) > 0
        
        # Check result structure
        for slot_name, result in results.items():
            assert "value_id" in result
            assert "value" in result
            if "color" in result:  # Some slots don't have colors
                assert isinstance(result["color"], (str, type(None)))


class TestPromptAPI:
    """Test prompt generation endpoints."""
    
    def test_generate_prompt(self):
        """Test POST /api/generate-prompt endpoint."""
        # Create a simple slot configuration
        slots = {
            "hair_style": {
                "enabled": True,
                "value_id": "ponytail",
                "value": "ponytail",
                "color": None,
                "weight": 1.0
            },
            "upper_body": {
                "enabled": True,
                "value_id": "shirt",
                "value": "shirt",
                "color": "blue",
                "weight": 1.0
            }
        }
        
        response = client.post(
            "/api/generate-prompt",
            json={
                "slots": slots,
                "full_body_mode": False,
                "upper_body_mode": False,
                "output_language": "en"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "prompt" in data
        assert isinstance(data["prompt"], str)
        assert len(data["prompt"]) > 0
        
        # Prompt should start with "1girl"
        assert data["prompt"].startswith("1girl")
        
    def test_generate_prompt_with_weights(self):
        """Test prompt generation with weight syntax."""
        slots = {
            "upper_body": {
                "enabled": True,
                "value_id": "blouse",
                "value": "blouse",
                "color": "blue",
                "weight": 1.5  # Non-default weight
            }
        }
        
        response = client.post(
            "/api/generate-prompt",
            json={
                "slots": slots,
                "full_body_mode": False,
                "upper_body_mode": False,
                "output_language": "en"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        # Check for weight syntax - note: weight formatting uses :1.5 not :1.50
        assert ":1.5" in data["prompt"] or "(blue blouse:1.5)" in data["prompt"]


class TestConfigsAPI:
    """Test configuration save/load endpoints."""
    
    def test_list_configs(self):
        """Test GET /api/configs endpoint."""
        response = client.get("/api/configs")
        assert response.status_code == 200
        
        data = response.json()
        assert "configs" in data
        assert isinstance(data["configs"], list)
        
    def test_save_and_load_config(self):
        """Test saving and loading a configuration."""
        config_name = "test_config_api"
        config_data = {
            "slots": {
                "hair_style": {
                    "enabled": True,
                    "value_id": "test_hair",
                    "color": None,
                    "weight": 1.0
                }
            }
        }
        
        # Save configuration
        response = client.post(
            f"/api/configs/{config_name}",
            json={
                "name": config_name,
                "data": config_data
            }
        )
        assert response.status_code == 200
        
        # List configurations to verify it was saved
        response = client.get("/api/configs")
        data = response.json()
        assert config_name in data["configs"]
        
        # Load the configuration
        response = client.get(f"/api/configs/{config_name}")
        assert response.status_code == 200
        
        loaded_data = response.json()
        assert loaded_data["name"] == config_name
        assert "data" in loaded_data
        assert "slots" in loaded_data["data"]
        assert "hair_style" in loaded_data["data"]["slots"]
        
        # Clean up - delete the test config
        # Note: The API doesn't have a delete endpoint, so we'll just
        # verify the save worked and leave cleanup to manual process
        # or the test environment setup/teardown


class TestParserAPI:
    """Test prompt parsing endpoint."""
    
    def test_parse_prompt(self):
        """Test POST /api/parse-prompt endpoint."""
        test_prompt = "1girl, blue shirt, ponytail"
        
        response = client.post(
            "/api/parse-prompt",
            json={
                "prompt": test_prompt,
                "use_fuzzy": True
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "slots" in data
        assert "unmatched" in data
        assert "matched_count" in data
        assert "total_tokens" in data
        assert "confidence" in data
        
        # Check structure of parsed slots
        slots = data["slots"]
        for slot_name, slot_data in slots.items():
            assert "value_id" in slot_data or "value" in slot_data
            assert "confidence" in slot_data
            assert "enabled" in slot_data
            
            if "color" in slot_data:
                assert isinstance(slot_data["color"], (str, type(None)))
            if "weight" in slot_data:
                assert isinstance(slot_data["weight"], (int, float))


class TestStaticFiles:
    """Test static file serving."""
    
    def test_index_html(self):
        """Test that the main page loads."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "<html" in response.text.lower() or "<!doctype html" in response.text.lower()
        
    def test_static_js(self):
        """Test that JavaScript files are served."""
        response = client.get("/static/js/app.js")
        assert response.status_code == 200
        assert "application/javascript" in response.headers["content-type"] or "text/javascript" in response.headers["content-type"]
        
    def test_static_css(self):
        """Test that CSS files are served."""
        response = client.get("/static/css/variables.css")
        assert response.status_code == 200
        assert "text/css" in response.headers["content-type"]


class TestErrorHandling:
    """Test error handling in API."""
    
    def test_invalid_endpoint(self):
        """Test response for invalid endpoint."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
        
    def test_malformed_json(self):
        """Test handling of malformed JSON."""
        response = client.post(
            "/api/generate-prompt",
            data="not json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422  # Unprocessable Entity
        
    def test_invalid_slot_data(self):
        """Test handling of invalid slot data."""
        response = client.post(
            "/api/generate-prompt",
            json={
                "slots": {
                    "invalid_slot": {
                        "enabled": True,
                        "value_id": "test"
                    }
                },
                "full_body_mode": False,
                "upper_body_mode": False,
                "output_language": "en"
            }
        )
        # Should still process, just ignore invalid slots
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])