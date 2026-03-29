using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace CommonService.Models.Interface
{
    public interface IUserTracking
    {
        string CreatedBy { get; set; }
        string? LastModifiedBy { get; set; }
    }
}