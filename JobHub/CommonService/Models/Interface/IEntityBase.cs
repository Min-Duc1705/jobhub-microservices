using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace CommonService.Models.Interface
{
    public interface IEntityBase<T>
    {
        T Id { get; set; }
    }
}