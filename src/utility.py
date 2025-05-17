import asyncio
import logging
from typing import Tuple  # Đã có trong Database
from datetime import datetime  # Đã có trong Database

# Import lớp Database và hàm get_database từ file của bạn
# Giả sử file database.py nằm cùng cấp hoặc trong PYTHONPATH
from database import Database, get_database

# Giả sử bạn có models.py định nghĩa các Pydantic models
# from models import Road # Nếu bạn có Pydantic model cho Road

# Thiết lập logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("traffic_control")


def calculate_cycle_and_green_times_2_phase(
    flow_ns: float,
    flow_ew: float,
    saturation_flow_ns: float,
    saturation_flow_ew: float,
    lost_time_per_phase: float = 4.0,
    min_cycle_time: float = 30.0,
    max_cycle_time: float = 120.0
    ) -> tuple[float, float, float]:
    """
    Trả về:
    - Chu kỳ đèn (giây)
    - Thời gian đèn xanh pha Bắc-Nam (giây)
    - Thời gian đèn xanh pha Đông-Tây (giây)
    """
    # Tỷ lệ lưu lượng
    y_ns = flow_ns / saturation_flow_ns if saturation_flow_ns > 0 else 0
    y_ew = flow_ew / saturation_flow_ew if saturation_flow_ew > 0 else 0
    Y = y_ns + y_ew
    num_phases = 2
    L = lost_time_per_phase * num_phases

    # Tính chu kỳ
    if Y >= 0.95:
        print(f"Cảnh báo: Giao lộ gần hoặc quá bão hòa (Y = {Y:.2f}). Sử dụng chu kỳ tối đa.")
        C = max_cycle_time
    elif Y <= 0:
        print("Thông tin: Không có luồng xe hoặc Y không hợp lệ. Sử dụng chu kỳ tối thiểu.")
        C = min_cycle_time
    else:
        C = (1.5 * L + 5) / (1 - Y)
        C = max(min_cycle_time, min(C, max_cycle_time))

    # Tính thời gian đèn xanh từng pha
    effective_green = C - L
    g_ns = (y_ns / Y) * effective_green if Y > 0 else effective_green / 2
    # g_ew = (y_ew / Y) * effective_green if Y > 0 else effective_green / 2

    return round(C), round(g_ns), round(C) - round(g_ns)


class FullRoad:
    def __init__(self, road_id: str, road_name: str, db_instance: Database, is_auto_control_lights: bool = False):
        self.road_id = road_id
        self.road_name = road_name  # Thêm tên để logging dễ hiểu hơn
        self.db = db_instance
        self.is_auto_control_lights = is_auto_control_lights
        self._auto_control_task: asyncio.Task | None = None
        # Các tham số có thể cấu hình cho mỗi road, hoặc lấy từ DB
        self.saturation_flow_ns = 1800.0  # xe/giờ
        self.saturation_flow_ew = 1800.0  # xe/giờ
        self.lost_time_per_phase = 4.0  # giây

    async def _get_flow_rates(self) -> Tuple[float, float]:
        try:
            flow_data = await self.db.get_aggregated_counts_for_a_road_and_compute_vehicle_per_hour(self.road_id)
            flow_ns_per_hour = flow_data.get("North-South", 0.0)
            flow_ew_per_hour = flow_data.get("East-West", 0.0)

            logger.warning(
                f"Road [{self.road_name} ({self.road_id})]: Đang sử dụng flow rates giả định. Cần cập nhật _get_flow_rates() với logic DB thực tế.")
            # Ví dụ ngẫu nhiên để thấy sự thay đổi
            logger.info(
                f"Road [{self.road_name} ({self.road_id})]: Lưu lượng giả định: NS={flow_ns_per_hour} veh/h, EW={flow_ew_per_hour} veh/h")
            return float(flow_ns_per_hour), float(flow_ew_per_hour)

        except Exception as e:
            logger.error(f"Road [{self.road_name} ({self.road_id})]: Lỗi khi lấy flow rates: {e}", exc_info=True)
            return 0.0, 0.0  # Trả về 0 nếu có lỗi

    async def _calculate_and_apply_lights(self):
        flow_ns, flow_ew = await self._get_flow_rates()

        cycle_time, green_time_ns, green_time_ew = calculate_cycle_and_green_times_2_phase(
            flow_ns, flow_ew,
            self.saturation_flow_ns, self.saturation_flow_ew,
            self.lost_time_per_phase
        )
        logger.info(
            f"Road [{self.road_name} ({self.road_id})]: Chu kỳ mới: C={cycle_time}s, G_NS={green_time_ns}s, G_EW={green_time_ew}s")

        # TODO: Gửi thông tin chu kỳ và thời gian xanh đến thiết bị đèn thực tế

        logger.info(f"Road [{self.road_name} ({self.road_id})]: Áp dụng (giả lập) cấu hình đèn mới.")
        return cycle_time  # Trả về chu kỳ để biết sleep bao lâu

    async def start_auto_control(self):
        if not self.is_auto_control_lights:
            logger.warning(
                f"Road [{self.road_name} ({self.road_id})]: start_auto_control được gọi nhưng is_auto_control_lights là False.")
            return

        logger.info(f"Road [{self.road_name} ({self.road_id})]: Bắt đầu chế độ tự động.")
        try:
            while self.is_auto_control_lights:
                cycle_time = await self._calculate_and_apply_lights()

                sleep_duration = max(10.0, float(cycle_time))  # Ngủ ít nhất 10s, hoặc theo chu kỳ
                logger.info(
                    f"Road [{self.road_name} ({self.road_id})]: Chờ {sleep_duration} giây trước khi tính toán lại...")
                await asyncio.sleep(sleep_duration)
        except asyncio.CancelledError:
            logger.info(f"Road [{self.road_name} ({self.road_id})]: Chế độ tự động đã bị hủy.")
        except Exception as e:
            logger.error(f"Road [{self.road_name} ({self.road_id})]: Lỗi trong start_auto_control: {e}", exc_info=True)
        finally:
            logger.info(f"Road [{self.road_name} ({self.road_id})]: Kết thúc vòng lặp tự động.")

    def request_stop_auto_control(self):
        logger.info(f"Road [{self.road_name} ({self.road_id})]: Yêu cầu dừng chế độ tự động.")
        self.is_auto_control_lights = False
        if self._auto_control_task and not self._auto_control_task.done():
            logger.info(f"Road [{self.road_name} ({self.road_id})]: Hủy task điều khiển tự động.")
            self._auto_control_task.cancel()
        else:
            logger.info(
                f"Road [{self.road_name} ({self.road_id})]: Không có task điều khiển tự động đang chạy hoặc đã xong.")


class RoadManager:
    def __init__(self, db_instance: Database):
        self.db = db_instance
        self.dict_road: dict[str, FullRoad] = {}

    async def initialize_roads(self):
        logger.info("RoadManager: Khởi tạo danh sách các nút giao thông từ DB...")
        try:
            # Sử dụng hàm get_all_roads từ lớp Database của bạn
            all_roads_data = await self.db.get_all_roads()  # Trả về List[dict]
            if not all_roads_data:
                logger.warning("RoadManager: Không tìm thấy nút giao thông nào trong cơ sở dữ liệu.")
                return

            for road_data in all_roads_data:
                road_id = str(road_data.get("_id"))  # Hoặc road_data.get("id") nếu đã được chuyển đổi
                road_name = road_data.get("name", f"UnknownRoad-{road_id}")  # Lấy tên, hoặc mặc định

                # Kiểm tra xem nút giao này có nên được điều khiển tự động mặc định không
                # Giả sử có trường 'auto_control_enabled' hoặc 'mode' trong road_data
                is_auto_default = road_data.get("auto_control_enabled", False)  # Mặc định là False

                if road_id:
                    self.dict_road[road_id] = FullRoad(road_id, road_name, self.db,
                                                       is_auto_control_lights=is_auto_default)
                    logger.info(
                        f"RoadManager: Đã tải nút giao: {road_name} ({road_id}), chế độ tự động mặc định: {is_auto_default}")
                    if is_auto_default:
                        await self.invoke_auto_control(road_id)
                else:
                    logger.warning(f"RoadManager: Bỏ qua bản ghi road không có _id: {road_data}")
            logger.info(f"RoadManager: Đã tải {len(self.dict_road)} nút giao thông.")

        except Exception as e:
            logger.error(f"RoadManager: Lỗi nghiêm trọng khi khởi tạo các nút giao: {e}", exc_info=True)
            # Tùy thuộc vào ứng dụng, bạn có thể muốn raise lỗi này để dừng khởi động FastAPI

    async def invoke_auto_control(self, road_id: str):
        if road_id not in self.dict_road:
            logger.error(f"RoadManager: Không tìm thấy road_id: {road_id} để kích hoạt tự động.")
            raise ValueError(f"Road ID {road_id} not found.")  # Sẽ thành HTTPException trong FastAPI

        road_obj = self.dict_road[road_id]
        if road_obj.is_auto_control_lights and road_obj._auto_control_task and not road_obj._auto_control_task.done():
            logger.info(
                f"RoadManager: Chế độ tự động đã được kích hoạt và đang chạy cho {road_obj.road_name} ({road_id}).")
            return

        # Hủy task cũ nếu có và chưa xong (dù hiếm khi xảy ra ở đây nếu logic đúng)
        if road_obj._auto_control_task and not road_obj._auto_control_task.done():
            logger.warning(f"RoadManager: Phát hiện task tự động cũ cho {road_obj.road_name} ({road_id}). Hủy bỏ...")
            road_obj._auto_control_task.cancel()
            try:
                await road_obj._auto_control_task  # Chờ task cũ bị hủy
            except asyncio.CancelledError:
                pass  # Mong đợi

        road_obj.is_auto_control_lights = True  # Đặt cờ TRƯỚC KHI tạo task mới
        logger.info(f"RoadManager: Kích hoạt chế độ điều khiển tự động cho {road_obj.road_name} ({road_id}).")
        road_obj._auto_control_task = asyncio.create_task(road_obj.start_auto_control())

    async def invoke_manual_control(self, road_id: str):
        if road_id not in self.dict_road:
            logger.error(f"RoadManager: Không tìm thấy road_id: {road_id} để kích hoạt thủ công.")
            raise ValueError(f"Road ID {road_id} not found.")

        road_obj = self.dict_road[road_id]
        if not road_obj.is_auto_control_lights and (
                not road_obj._auto_control_task or road_obj._auto_control_task.done()):
            logger.info(
                f"RoadManager: Chế độ thủ công đã được kích hoạt (hoặc tự động chưa chạy/đã dừng) cho {road_obj.road_name} ({road_id}).")
            return

        logger.info(
            f"RoadManager: Kích hoạt chế độ điều khiển thủ công cho {road_obj.road_name} ({road_id}). Dừng chế độ tự động...")
        road_obj.request_stop_auto_control()

        if road_obj._auto_control_task:
            try:
                await asyncio.wait_for(road_obj._auto_control_task, timeout=10.0)  # Tăng timeout
                logger.info(f"RoadManager: Task tự động cho {road_obj.road_name} ({road_id}) đã dừng thành công.")
            except asyncio.CancelledError:
                logger.info(
                    f"RoadManager: Task tự động cho {road_obj.road_name} ({road_id}) đã được hủy (trong invoke_manual_control).")
            except asyncio.TimeoutError:
                logger.warning(
                    f"RoadManager: Timeout khi chờ task tự động cho {road_obj.road_name} ({road_id}) dừng. Task có thể vẫn đang chạy ngầm nếu không xử lý CancelledError đúng cách.")
            except Exception as e:
                logger.error(f"RoadManager: Lỗi khi chờ task tự động cho {road_obj.road_name} ({road_id}) dừng: {e}",
                             exc_info=True)
            road_obj._auto_control_task = None

    async def shutdown(self):
        logger.info("RoadManager: Bắt đầu quá trình tắt...")
        tasks_to_wait = []
        for road_id, road_obj in self.dict_road.items():
            if road_obj.is_auto_control_lights and road_obj._auto_control_task and not road_obj._auto_control_task.done():
                logger.info(f"RoadManager: Dừng điều khiển tự động cho {road_obj.road_name} ({road_id}) khi tắt.")
                road_obj.request_stop_auto_control()
                if road_obj._auto_control_task:
                    tasks_to_wait.append(road_obj._auto_control_task)

        if tasks_to_wait:
            logger.info(f"RoadManager: Chờ {len(tasks_to_wait)} task điều khiển tự động hoàn tất...")
            results = await asyncio.gather(*tasks_to_wait, return_exceptions=True)
            for i, result in enumerate(results):
                task_description = f"Task_{i}"  # Cần cách tốt hơn để xác định task nào
                if hasattr(tasks_to_wait[i], 'get_coro') and hasattr(tasks_to_wait[i].get_coro(), '__qualname__'):
                    task_description = tasks_to_wait[i].get_coro().__qualname__

                if isinstance(result, asyncio.CancelledError):
                    logger.info(f"RoadManager: {task_description} đã được hủy thành công khi tắt.")
                elif isinstance(result, Exception):
                    logger.error(f"RoadManager: {task_description} gặp lỗi khi tắt: {result}",
                                 exc_info=isinstance(result, BaseException))
        logger.info("RoadManager: Đã tắt.")


# --- Test độc lập (nếu cần) ---
async def standalone_main():
    logger.info("--- Bắt đầu kiểm tra độc lập RoadManager ---")

    # Khởi tạo DB
    db = get_database()  # Sử dụng hàm get_database của bạn
    if not db.client:
        logger.error("Không thể kết nối tới MongoDB. Vui lòng kiểm tra connection_string và MongoDB server.")
        return

    logger.info("Kết nối Database thành công.")

    # Khởi tạo RoadManager
    manager = RoadManager(db)
    await manager.initialize_roads()

    if not manager.dict_road:
        logger.warning("Không có nút giao nào được tải. Kết thúc kiểm tra.")
        # Đóng client nếu cần
        # db.client.close() # Motor client không cần close() tường minh trong nhiều trường hợp
        return

    # Lấy một road_id để thử nghiệm (nếu có)
    test_road_id = list(manager.dict_road.keys())[0]
    logger.info(f"Sử dụng road_id: {test_road_id} ({manager.dict_road[test_road_id].road_name}) để kiểm tra.")

    try:
        logger.info(f"--- Kích hoạt tự động cho {test_road_id} ---")
        await manager.invoke_auto_control(test_road_id)

        logger.info("Chờ 15 giây để chế độ tự động chạy...")
        await asyncio.sleep(15)  # Cho phép 1-2 chu kỳ chạy

        logger.info(f"--- Chuyển {test_road_id} sang thủ công ---")
        await manager.invoke_manual_control(test_road_id)

        logger.info("Chờ 5 giây ở chế độ thủ công...")
        await asyncio.sleep(5)

        logger.info(f"--- Kích hoạt lại tự động cho {test_road_id} ---")
        await manager.invoke_auto_control(test_road_id)

        logger.info("Chờ 15 giây nữa...")
        await asyncio.sleep(15)

    except KeyboardInterrupt:
        logger.info("Đã nhận Ctrl+C. Bắt đầu tắt...")
    except Exception as e:
        logger.error(f"Lỗi không mong muốn trong quá trình kiểm tra: {e}", exc_info=True)
    finally:
        logger.info("--- Kết thúc kiểm tra. Đang tắt RoadManager ---")
        await manager.shutdown()
        # db.client.close() # Xem xét việc đóng client ở đây nếu cần
        logger.info("--- RoadManager đã tắt. Kiểm tra hoàn tất ---")


if __name__ == "__main__":
    # Cấu hình để chạy standalone_main
    # Đảm bảo `settings.mongodb_url` trong `config.py` của bạn là đúng.
    # File database.py và config.py cần nằm trong PYTHONPATH hoặc cùng thư mục.

    # Kiểm tra xem `get_database` có được gọi từ đâu đó để `_db` được khởi tạo không
    # Nếu không, gọi nó một lần ở đây trước khi vào `asyncio.run` nếu `get_database`
    # của bạn có logic khởi tạo khi gọi lần đầu mà không phải trong context async.
    # Tuy nhiên, với `AsyncIOMotorClient` thì không sao.

    try:
        asyncio.run(standalone_main())
    except KeyboardInterrupt:
        logger.info("Chương trình bị ngắt bởi người dùng (KeyboardInterrupt ngoài asyncio.run).")