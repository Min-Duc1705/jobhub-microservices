using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace CommonService.Models
{
    
    public abstract class EntityBase<T> : IEntityBase<T>
    {
        public T Id { get; set; } = default!;
    }
}