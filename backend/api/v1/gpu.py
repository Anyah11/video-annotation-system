from fastapi import APIRouter

router = APIRouter(prefix="/api/gpu", tags=["gpu"])

# Try to import pynvml
try:
    import pynvml
    GPU_AVAILABLE = True
    pynvml.nvmlInit()
except:
    GPU_AVAILABLE = False
    print("Warning: NVIDIA GPU monitoring not available")


@router.get("/status")
def get_gpu_status():
    """Get status of all GPUs"""
    if not GPU_AVAILABLE:
        return {
            "available": False,
            "message": "GPU monitoring not available on this system",
            "gpus": []
        }
    
    try:
        device_count = pynvml.nvmlDeviceGetCount()
        gpus = []
        
        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            name = pynvml.nvmlDeviceGetName(handle)
            
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            memory_total = mem_info.total / (1024 ** 3)
            memory_used = mem_info.used / (1024 ** 3)
            memory_free = mem_info.free / (1024 ** 3)
            
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            gpu_util = util.gpu
            
            try:
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            except:
                temp = 0
            
            try:
                procs = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
                process_count = len(procs)
            except:
                process_count = 0
            
            gpus.append({
                "id": i,
                "name": name,
                "memory_total_gb": round(memory_total, 2),
                "memory_used_gb": round(memory_used, 2),
                "memory_free_gb": round(memory_free, 2),
                "memory_usage_percent": round((memory_used / memory_total) * 100, 1),
                "gpu_utilization_percent": gpu_util,
                "temperature_c": temp,
                "process_count": process_count,
                "available": gpu_util < 80 and memory_used < memory_total * 0.9
            })
        
        return {
            "available": True,
            "gpu_count": device_count,
            "gpus": gpus
        }
        
    except Exception as e:
        return {
            "available": False,
            "message": f"Error reading GPU status: {str(e)}",
            "gpus": []
        }
