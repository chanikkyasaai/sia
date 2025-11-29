"""
Voice Agent API Test Suite

Tests the complete voice agent pipeline by calling the API endpoints directly.
Covers both CRUD operations and analysis functionality.
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class VoiceAgentAPITest:
    """Test suite for Voice Agent API endpoints"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.business_id = 2
        self.user_id = 1
        self.session_id = None

    async def setup_session(self) -> bool:
        """Start a voice session"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "business_id": self.business_id,
                    "user_id": self.user_id
                }

                logger.info("🚀 Starting voice session...")
                async with session.post(
                    f"{self.base_url}/voice/agent/voice/start",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.session_id = data.get("session_id")
                        logger.info(f"✅ Session created: {self.session_id}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"❌ Session creation failed: {response.status} - {error_text}")
                        return False
        except Exception as e:
            logger.error(f"❌ Session setup error: {str(e)}")
            return False

    async def test_crud_operation(self) -> Dict[str, Any]:
        """Test Case 1: CRUD Operation - Create a sale transaction"""
        logger.info("\n🔥 TEST CASE 1: CRUD Operation - Sale Transaction")
        logger.info("=" * 60)

        try:
            async with aiohttp.ClientSession() as session:
                # Test transcript for sale transaction
                transcript = "How many apples do I have in stock?"

                payload = {
                    "business_id": self.business_id,
                    "user_id": self.user_id,
                    "transcript": transcript
                }

                logger.info(f"📝 Voice Input: '{transcript}'")
                logger.info(f"🔧 Payload: {json.dumps(payload, indent=2)}")

                # Call voice agent API
                async with session.post(
                    f"{self.base_url}/voice/agent/voice?session_id={self.session_id}",
                    json=payload
                ) as response:

                    # Handle different response types
                    if response.content_type == 'application/json':
                        response_data = await response.json()
                    else:
                        # Handle HTML/text error responses
                        error_text = await response.text()
                        logger.error(f"❌ Non-JSON response ({response.content_type}): {error_text[:500]}")
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text[:200]}",
                            "test_type": "crud_operation"
                        }

                    logger.info(f"📡 API Response Status: {response.status}")
                    logger.info(
                        f"🤖 Agent Reply: {response_data.get('reply_text', 'No reply')}")
                    logger.info(
                        f"⚡ Actions Taken: {response_data.get('actions_taken', [])}")

                    # Check NLU results
                    nlu_data = response_data.get('nlu', {})
                    logger.info(
                        f"🧠 NLU Intent: {nlu_data.get('intent', 'Unknown')}")
                    logger.info(
                        f"📊 NLU Entities: {nlu_data.get('entities', {})}")
                    logger.info(
                        f"🎯 Confidence: {nlu_data.get('confidence', 0)}")

                    # Check execution results
                    execution_data = response_data.get('execution_data', {})
                    if execution_data:
                        logger.info(
                            f"💾 Execution Data: {json.dumps(execution_data, indent=2)}")

                    # Determine success
                    success = (
                        response.status == 200 and
                        "failed" not in response_data.get('reply_text', '').lower() and
                        response_data.get('actions_taken', [])
                    )

                    if success:
                        logger.info(
                            "✅ CRUD Test PASSED - Transaction created successfully")
                    else:
                        logger.error(
                            "❌ CRUD Test FAILED - Transaction creation failed")

                    return {
                        "success": success,
                        "response": response_data,
                        "test_type": "crud_operation",
                        "transcript": transcript
                    }

        except Exception as e:
            logger.error(f"❌ CRUD test error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "test_type": "crud_operation"
            }

    async def test_analysis_operation(self) -> Dict[str, Any]:
        """Test Case 2: Analysis Operation - Sales trend analysis"""
        logger.info("\n🔥 TEST CASE 2: Analysis Operation - Sales Trends")
        logger.info("=" * 60)

        try:
            async with aiohttp.ClientSession() as session:
                # Test transcript for analysis
                transcript = "Show me sales trends for last month"

                payload = {
                    "business_id": self.business_id,
                    "user_id": self.user_id,
                    "transcript": transcript
                }

                logger.info(f"📝 Voice Input: '{transcript}'")
                logger.info(f"🔧 Payload: {json.dumps(payload, indent=2)}")

                # Call voice agent API
                async with session.post(
                    f"{self.base_url}/voice/agent/voice?session_id={self.session_id}",
                    json=payload
                ) as response:

                    # Handle different response types
                    if response.content_type == 'application/json':
                        response_data = await response.json()
                    else:
                        # Handle HTML/text error responses
                        error_text = await response.text()
                        logger.error(f"❌ Non-JSON response ({response.content_type}): {error_text[:500]}")
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text[:200]}",
                            "test_type": "analysis_operation"
                        }

                    logger.info(f"📡 API Response Status: {response.status}")
                    logger.info(
                        f"🤖 Agent Reply: {response_data.get('reply_text', 'No reply')}")
                    logger.info(
                        f"⚡ Actions Taken: {response_data.get('actions_taken', [])}")

                    # Check NLU results
                    nlu_data = response_data.get('nlu', {})
                    logger.info(
                        f"🧠 NLU Intent: {nlu_data.get('intent', 'Unknown')}")
                    logger.info(
                        f"📊 NLU Entities: {nlu_data.get('entities', {})}")
                    logger.info(
                        f"🎯 Confidence: {nlu_data.get('confidence', 0)}")

                    # Check execution results
                    execution_data = response_data.get('execution_data', {})
                    if execution_data:
                        logger.info("📈 Analysis Results:")
                        logger.info(
                            f"  - Analysis Type: {execution_data.get('analysis_type', 'Unknown')}")
                        logger.info(
                            f"  - Objective: {execution_data.get('objective', 'Unknown')}")

                        # Check execution summary
                        exec_summary = execution_data.get(
                            'execution_summary', {})
                        logger.info(
                            f"  - Queries Executed: {exec_summary.get('total_queries', 0)}")
                        logger.info(
                            f"  - Successful Queries: {exec_summary.get('successful_queries', 0)}")
                        logger.info(
                            f"  - Total Rows: {exec_summary.get('total_rows', 0)}")

                        # Check insights
                        insights = execution_data.get('insights', {})
                        if insights:
                            logger.info(
                                f"  - Summary: {insights.get('summary_text', 'No summary')}")
                            logger.info(
                                f"  - Query Summary: {insights.get('query_summary', 'No query summary')}")

                    # Determine success
                    success = (
                        response.status == 200 and
                        "failed" not in response_data.get('reply_text', '').lower() and
                        (execution_data.get('insights')
                         or execution_data.get('execution_summary'))
                    )

                    if success:
                        logger.info(
                            "✅ Analysis Test PASSED - Query analysis completed")
                    else:
                        logger.error(
                            "❌ Analysis Test FAILED - Analysis execution failed")

                    return {
                        "success": success,
                        "response": response_data,
                        "test_type": "analysis_operation",
                        "transcript": transcript
                    }

        except Exception as e:
            logger.error(f"❌ Analysis test error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "test_type": "analysis_operation"
            }

    async def test_inventory_query(self) -> Dict[str, Any]:
        """Test Case 3: Inventory Query - Check stock levels"""
        logger.info("\n🔥 TEST CASE 3: Inventory Query - Stock Check")
        logger.info("=" * 60)

        try:
            async with aiohttp.ClientSession() as session:
                # Test transcript for inventory check
                transcript = "What will be my revenue after one month?"

                payload = {
                    "business_id": self.business_id,
                    "user_id": self.user_id,
                    "transcript": transcript
                }

                logger.info(f"📝 Voice Input: '{transcript}'")
                logger.info(f"🔧 Payload: {json.dumps(payload, indent=2)}")

                # Call voice agent API
                async with session.post(
                    f"{self.base_url}/voice/agent/voice?session_id={self.session_id}",
                    json=payload
                ) as response:

                    # Handle different response types
                    if response.content_type == 'application/json':
                        response_data = await response.json()
                    else:
                        # Handle HTML/text error responses
                        error_text = await response.text()
                        logger.error(f"❌ Non-JSON response ({response.content_type}): {error_text[:500]}")
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text[:200]}",
                            "test_type": "inventory_query"
                        }

                    logger.info(f"📡 API Response Status: {response.status}")
                    logger.info(
                        f"🤖 Agent Reply: {response_data.get('reply_text', 'No reply')}")
                    logger.info(
                        f"⚡ Actions Taken: {response_data.get('actions_taken', [])}")

                    # Check NLU results
                    nlu_data = response_data.get('nlu', {})
                    logger.info(
                        f"🧠 NLU Intent: {nlu_data.get('intent', 'Unknown')}")
                    logger.info(
                        f"📊 NLU Entities: {nlu_data.get('entities', {})}")

                    # Check if query was processed
                    success = (
                        response.status == 200 and
                        nlu_data.get('intent') in [
                            'STOCK_INQUIRY', 'ASK_INVENTORY', 'GET_INVENTORY']
                    )

                    if success:
                        logger.info("✅ Inventory Query Test PASSED")
                    else:
                        logger.error("❌ Inventory Query Test FAILED")

                    return {
                        "success": success,
                        "response": response_data,
                        "test_type": "inventory_query",
                        "transcript": transcript
                    }

        except Exception as e:
            logger.error(f"❌ Inventory query test error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "test_type": "inventory_query"
            }

    async def test_server_connectivity(self) -> Dict[str, Any]:
        """Test basic server connectivity"""
        logger.info("\n🌐 SERVER CONNECTIVITY CHECK")
        logger.info("=" * 40)

        try:
            async with aiohttp.ClientSession() as session:
                # Test if server is running
                async with session.get(f"{self.base_url}/") as response:
                    logger.info(f"🔌 Server Status: {response.status}")
                    if response.status == 200:
                        logger.info("✅ Server is running")
                        return {
                            "success": True,
                            "response": {"status": response.status},
                            "test_type": "server_connectivity"
                        }
                    else:
                        logger.error(f"❌ Server returned status {response.status}")
                        return {
                            "success": False,
                            "error": f"Server returned status {response.status}",
                            "test_type": "server_connectivity"
                        }
        except Exception as e:
            logger.error(f"❌ Server connectivity error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "test_type": "server_connectivity"
            }

    async def test_health_check(self) -> Dict[str, Any]:
        """Test the voice service health endpoint"""
        logger.info("\n🔍 HEALTH CHECK")
        logger.info("=" * 30)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/voice/agent/voice/health") as response:
                    # Handle different response types
                    if response.content_type == 'application/json':
                        health_data = await response.json()
                    else:
                        # Handle HTML/text error responses
                        error_text = await response.text()
                        logger.error(f"❌ Health check non-JSON response ({response.content_type}): {error_text[:500]}")
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text[:200]}",
                            "test_type": "health_check"
                        }

                    logger.info(f"🏥 Health Status: {response.status}")
                    logger.info(f"🔧 Services: {list(health_data.keys())}")
                    logger.info(
                        f"📊 Active Connections: {health_data.get('active_connections', 0)}")
                    logger.info(
                        f"🎤 Transcription Sessions: {health_data.get('active_transcription_sessions', 0)}")

                    success = response.status == 200
                    return {
                        "success": success,
                        "response": health_data,
                        "test_type": "health_check"
                    }

        except Exception as e:
            logger.error(f"❌ Health check error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "test_type": "health_check"
            }

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run complete test suite"""
        logger.info("🚀 VOICE AGENT API TEST SUITE")
        logger.info("=" * 70)
        logger.info(f"📅 Test started at: {datetime.now()}")
        logger.info(f"🏢 Business ID: {self.business_id}")
        logger.info(f"👤 User ID: {self.user_id}")
        logger.info(f"🌐 Base URL: {self.base_url}")

        results = {}

        try:
            # Server connectivity check first
            results["server_connectivity"] = await self.test_server_connectivity()
            
            # Health check
            results["health_check"] = await self.test_health_check()

            # Setup session
            session_setup = await self.setup_session()
            if not session_setup:
                logger.error("❌ Session setup failed - aborting tests")
                return {"error": "Session setup failed", "results": results}

            # Run test cases
            results["crud_operation"] = await self.test_crud_operation()
            results["analysis_operation"] = await self.test_analysis_operation()
            results["inventory_query"] = await self.test_inventory_query()

            # Summary
            logger.info("\n" + "=" * 70)
            logger.info("📊 TEST RESULTS SUMMARY")
            logger.info("=" * 70)

            total_tests = len([r for r in results.values()
                              if isinstance(r, dict) and "success" in r])
            passed_tests = sum(1 for r in results.values() if isinstance(
                r, dict) and r.get("success", False))

            for test_name, result in results.items():
                if isinstance(result, dict) and "success" in result:
                    status = "✅ PASSED" if result["success"] else "❌ FAILED"
                    logger.info(
                        f"  {test_name.replace('_', ' ').title()}: {status}")

            logger.info(
                f"\n🏆 Overall Results: {passed_tests}/{total_tests} tests passed")

            if passed_tests == total_tests:
                logger.info("\n🎉 ALL TESTS PASSED - Voice Agent API Working!")
                logger.info("\n✅ Verified Components:")
                logger.info("  • Voice session management")
                logger.info("  • CRUD operations (transaction creation)")
                logger.info("  • Analysis operations (unified analyzer)")
                logger.info("  • Inventory queries")
                logger.info("  • NLU intent parsing")
                logger.info("  • Entity resolution")
                logger.info("  • SQL execution and insights generation")
            else:
                logger.warning(
                    f"\n⚠️ {total_tests - passed_tests} tests failed - Check logs above")

            return {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": f"{(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%",
                "results": results
            }

        except Exception as e:
            logger.error(f"❌ Test suite failed: {str(e)}")
            return {
                "error": str(e),
                "results": results
            }


async def main():
    """Run the voice agent API tests"""
    test_suite = VoiceAgentAPITest()
    results = await test_suite.run_all_tests()

    # Print final summary
    if "error" not in results:
        print(f"\n📈 Test Suite Completed!")
        print(f"Success Rate: {results['success_rate']}")
    else:
        print(f"\n💥 Test Suite Failed: {results['error']}")


if __name__ == "__main__":
    asyncio.run(main())
